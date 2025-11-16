import json
import os
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from threading import Lock
from typing import Optional

import requests
from pydantic import Field, validate_call
from tenacity import retry, stop_after_attempt, wait_random
from tqdm import tqdm

from .md5 import check_hash


@retry(stop=stop_after_attempt(10), wait=wait_random(min=1, max=5))
def get_final_url(url: str, headers: dict) -> str:
    response = requests.head(url, allow_redirects=True, headers=headers)
    return response.url


@retry(stop=stop_after_attempt(10), wait=wait_random(min=1, max=5))
def download_chunk(
    url: str,
    headers: dict,
    start: int,
    end: int,
    file_path: str,
    thread_id: int,
    progress_bar,
    meta_lock: Lock,
    meta_path: str,
    meta_data: dict,
):
    meta_key = f"{start}-{end}"
    meta_info = meta_data.get(
        meta_key,
        {
            "status": "pending",
            "size": end - start + 1,
            "start": start,
            "end": end,
            "thread_id": thread_id,
            "retry_count": 0,
            "last_status_code": None,
            "error": None,
        },
    )

    if meta_info.get("status") == "done":
        progress_bar.update(meta_info.get("size", end - start + 1))
        return

    try:
        meta_info["thread_id"] = thread_id
        meta_info["retry_count"] += 1
        meta_info["last_status_code"] = None

        thread_headers = headers.copy()
        thread_headers.update({"Range": f"bytes={start}-{end}"})
        response = requests.get(url, headers=thread_headers, stream=True)

        meta_info["last_status_code"] = response.status_code

        if response.status_code in [200, 206]:
            content_range = response.headers.get("Content-Range", "")
            expected_prefix = f"bytes {start}-{end}"
            if not content_range.startswith(expected_prefix):
                raise Exception(f"线程 {thread_id}: Content-Range 错误, 预期开头 {expected_prefix}, 实际 {content_range}")

            total_written = 0
            chunk_size = 8192
            with meta_lock:
                with open(file_path, "r+b") as f:
                    f.seek(start)
                    for chunk in response.iter_content(chunk_size=chunk_size):
                        if chunk:
                            f.write(chunk)
                            total_written += len(chunk)
                            progress_bar.update(len(chunk))

            meta_info["status"] = "done"
            meta_info["error"] = None
            meta_info["size"] = total_written

            with meta_lock:
                meta_data[meta_key] = meta_info
                with open(meta_path, "w", encoding="utf-8") as mf:
                    json.dump(meta_data, mf, indent=2)
        else:
            raise Exception(f"线程 {thread_id}: 状态码 {response.status_code}")

    except Exception as e:
        meta_info["status"] = "error"
        meta_info["error"] = str(e)
        with meta_lock:
            meta_data[meta_key] = meta_info
            with open(meta_path, "w", encoding="utf-8") as mf:
                json.dump(meta_data, mf, indent=2)
        raise


@validate_call
def download_file(
    url: str,
    output_path: str | Path,
    headers: Optional[dict] = None,
    overwrite: bool = False,
    verbose: bool = True,
    block_size: int = Field(default=10, ge=1, le=100),
    num_threads: int = 4,
    expected_md5: Optional[str] = None,
) -> None:
    """
    下载文件, 支持断点续传和多线程下载.

    Args:
        url (str): 文件的下载链接.
        output_path (str): 下载后保存的文件路径.
        headers (dict, optional): 请求头, 如果不提供, 将使用默认的请求头.
        overwrite (bool, optional): 是否覆盖已存在的文件, 默认为 False.
        verbose (bool, optional): 是否打印下载进度, 默认为 True.
        block_size (int, optional): 每个线程下载的块大小(MB), 默认为 50MB.
        num_threads (int, optional): 线程数, 默认为 4.
        expected_md5 (str, optional): 预期的 MD5 校验和, 默认为 None表示不进行校验.

    Raises:
        ValueError: 如果 MD5 校验失败, 将引发此异常.

    Returns:
        None
    """
    if isinstance(output_path, Path):
        output_path = str(output_path)

    if headers is None:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/136.0.0.0 Safari/537.36 Edg/136.0.0.0"
            )
        }

    meta_path = output_path + ".meta"
    # is_xuchuan = False
    if os.path.exists(output_path):
        if overwrite:
            if os.path.exists(meta_path):
                if verbose:
                    print(f"文件 {output_path} 已存在, 准备覆盖. ")
                os.remove(meta_path)
            os.remove(output_path)
        else:
            if os.path.exists(meta_path):
                if verbose:
                    print(f"文件 {output_path} 已存在,且存在元数据, 准备续传. ")
                with open(meta_path, "r", encoding="utf-8") as mf:
                    meta_data = json.load(mf)
                completed_bytes = sum(info["size"] for info in meta_data.values() if info.get("status") == "done")
                if completed_bytes > 0:
                    if verbose:
                        print(f"已完成 {completed_bytes} 字节, 准备继续下载. ")
                    with open(output_path, "ab") as f:
                        f.truncate(completed_bytes)
                    # is_xuchuan = True
            else:
                if verbose:
                    print("没有找到元数据, 且设置了不覆盖文件, 返回 None ")
                return
                # 证明该文件存在本地

    final_url = get_final_url(url, headers)
    if not final_url:
        print("❌ 无法获取最终的下载链接. ")
        return

    response = requests.head(final_url, headers=headers, allow_redirects=True)
    response.raise_for_status()
    file_size = int(response.headers.get("Content-Length", 0))

    if not os.path.exists(output_path):
        with open(output_path, "wb") as f:
            f.truncate(file_size)

    block_bytes = block_size * 1024 * 1024
    ranges = [(start, min(start + block_bytes - 1, file_size - 1)) for start in range(0, file_size, block_bytes)]

    if os.path.exists(meta_path):
        with open(meta_path, "r", encoding="utf-8") as mf:
            meta_data = json.load(mf)
    else:
        meta_data = {
            f"{start}-{end}": {
                "status": "pending",
                "start": start,
                "end": end,
                "size": end - start + 1,
                "thread_id": None,
                "retry_count": 0,
                "last_status_code": None,
                "error": None,
            }
            for start, end in ranges
        }
        with open(meta_path, "w", encoding="utf-8") as mf:
            json.dump(meta_data, mf, indent=2)

    completed_bytes = sum(info["size"] for info in meta_data.values() if info.get("status") == "done")

    progress_bar = tqdm(
        total=file_size,
        initial=completed_bytes,
        unit="B",
        unit_scale=True,
        desc="下载进度",
        disable=not verbose,
    )

    meta_lock = Lock()

    with ThreadPoolExecutor(max_workers=num_threads) as executor:
        futures = []
        for i, (start, end) in enumerate(ranges):
            futures.append(
                executor.submit(
                    download_chunk,
                    final_url,
                    headers,
                    start,
                    end,
                    output_path,
                    i,
                    progress_bar,
                    meta_lock,
                    meta_path,
                    meta_data,
                )
            )
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"❌ 下载失败: {e}")
                progress_bar.close()
                return

    progress_bar.close()

    if expected_md5:
        if not check_hash(output_path, expected_md5=expected_md5):
            raise ValueError(f"❌ MD5 校验失败: {output_path}")
        elif verbose:
            print("✅ MD5 校验通过. ")

    if all(info.get("status") == "done" for info in meta_data.values()):
        if os.path.exists(meta_path):
            os.remove(meta_path)
