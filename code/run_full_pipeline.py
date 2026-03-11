"""
MASTER DATA PIPELINE
====================
Single-script orchestration of the entire data pipeline:
  1. Fetch raw data (FRED, JODI, WDI)
  2. Convert IVT binary files to CSV
  3. Clean raw datasets
  4. Clean converted datasets
  5. Consolidate into processed panel
  6. Standardize dates
  7. Merge final analysis panel

Output: data/final/m1_panel.csv (ready for analysis)
        data/final/m1_metadata.txt
        data/final/m1_data_dictionary.csv
"""

from __future__ import annotations

import sys
from pathlib import Path

# Add code directory to path
PROJECT_ROOT = Path(__file__).resolve().parents[1]
CODE_DIR = PROJECT_ROOT / "code"
sys.path.insert(0, str(CODE_DIR))


def print_header(step_num: int, title: str) -> None:
    """Print a formatted step header."""
    print("\n" + "=" * 70)
    print(f"STEP {step_num}: {title}")
    print("=" * 70)


def run_pipeline() -> bool:
    """
    Execute the complete data pipeline.
    Returns True if successful, False otherwise.
    """
    
    try:
        # Step 1: Fetch raw data
        print_header(1, "FETCH RAW DATA")
        print("Fetching FRED, JODI, and WDI datasets...")
        from fetch_all_raw_data import main as fetch_main
        fetch_main()
        
        # Step 2: Convert IVT to tabular
        print_header(2, "CONVERT IVT BINARY FILES")
        print("Converting JODI IVT files to CSV format...")
        from convert_ivt_to_tabular import main as convert_main
        convert_main()
        
        # Step 3: Clean raw data
        print_header(3, "CLEAN RAW DATASETS")
        print("Applying data quality filters to raw datasets...")
        from clean_raw_data import main as clean_raw_main
        clean_raw_main()
        
        # Step 4: Clean converted IVT data
        print_header(4, "CLEAN CONVERTED IVT DATA")
        print("Applying data quality filters to converted IVT datasets...")
        from clean_converted_data import main as clean_converted_main
        clean_converted_main()
        
        # Step 5: Consolidate datasets
        print_header(5, "CONSOLIDATE DATASETS")
        print("Merging FRED, JODI, and WDI into single processed panel...")
        from consolidate_datasets import consolidate_datasets
        df_consolidated = consolidate_datasets()
        print(f"✅ Consolidated: {len(df_consolidated):,} rows × {len(df_consolidated.columns)} columns")
        
        # Step 6: Standardize dates
        print_header(6, "STANDARDIZE DATE COLUMNS")
        print("Converting all date columns to consistent format...")
        from standardize_dates_to_final import main as standardize_main
        standardize_main()
        
        # Step 7: Merge final panel
        print_header(7, "CREATE FINAL ANALYSIS PANEL")
        print("Generating final analysis-ready panel...")
        from merge_final_panel import main as merge_main
        merge_main()
        
        # Success summary
        print("\n" + "=" * 70)
        print("✅ PIPELINE COMPLETE")
        print("=" * 70)
        print("\nOutput files created:")
        final_dir = PROJECT_ROOT / "data" / "final"
        output_files = [
            final_dir / "m1_panel.csv",
            final_dir / "m1_metadata.txt",
            final_dir / "m1_data_dictionary.csv",
        ]
        for f in output_files:
            if f.exists():
                size = f.stat().st_size / (1024 * 1024)  # Convert to MB
                print(f"  ✓ {f.relative_to(PROJECT_ROOT)} ({size:.1f} MB)")
            else:
                print(f"  ✗ {f.relative_to(PROJECT_ROOT)} (NOT FOUND)")
        
        print("\n🎯 Ready for analysis!")
        return True
        
    except Exception as e:
        print("\n" + "=" * 70)
        print(f"❌ PIPELINE FAILED")
        print("=" * 70)
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        return False


def main() -> None:
    """Entry point."""
    print("\n" + "🚀 " * 15)
    print("MASTER DATA PIPELINE STARTING")
    print("🚀 " * 15)
    print(f"Project root: {PROJECT_ROOT}")
    print(f"Working directory: {Path.cwd()}")
    
    success = run_pipeline()
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
