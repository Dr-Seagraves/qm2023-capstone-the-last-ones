from __future__ import annotations

from io import BytesIO
from zipfile import ZipFile

import requests

from config_paths import RAW_DATA_DIR


JODI_WORLD_EXT_ZIP_URL = "https://www.jodidata.org/_resources/files/downloads/oil-data/world_ext.zip?iid=171"
JODI_GAS_WORLD_ZIP_URL = "https://www.jodidata.org/jodi-publisher/gas/16/GAS_world_NewFormat.zip"
JODI_GAS_IVT_ZIP_URL = "https://www.jodidata.org/jodi-publisher/gas/16/ivt-merged.zip"


def _download_and_extract_zip(url: str, zip_filename: str) -> tuple[int, int]:
    response = requests.get(url, timeout=120)
    response.raise_for_status()

    zip_path = RAW_DATA_DIR / zip_filename
    zip_path.write_bytes(response.content)
    print("Saved:", zip_path)

    extracted_count = 0
    with ZipFile(BytesIO(response.content)) as archive:
        for member_name in archive.namelist():
            target = RAW_DATA_DIR / member_name
            target.write_bytes(archive.read(member_name))
            extracted_count += 1
            print("Extracted:", target)

    return len(response.content), extracted_count


def fetch_jodi_data() -> dict[str, int]:
    oil_bytes, oil_files = _download_and_extract_zip(
        JODI_WORLD_EXT_ZIP_URL,
        "jodi_oil_world_ext_raw.zip",
    )
    gas_world_bytes, gas_world_files = _download_and_extract_zip(
        JODI_GAS_WORLD_ZIP_URL,
        "jodi_gas_world_newformat_raw.zip",
    )
    gas_ivt_bytes, gas_ivt_files = _download_and_extract_zip(
        JODI_GAS_IVT_ZIP_URL,
        "jodi_gas_ivt_merged_raw.zip",
    )

    return {
        "zip_bytes_total": oil_bytes + gas_world_bytes + gas_ivt_bytes,
        "extracted_files_total": oil_files + gas_world_files + gas_ivt_files,
    }


def main() -> None:
    counts = fetch_jodi_data()
    print("✅ JODI fetch complete")
    print("Downloaded bytes:", counts["zip_bytes_total"])
    print("Extracted files:", counts["extracted_files_total"])


if __name__ == "__main__":
    main()
