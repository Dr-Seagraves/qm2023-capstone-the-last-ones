# code/m1_data_pipeline.py

from fetch_reit_data import fetch_reit_data
from merge_final_panel import merge_final_panel


def main():
    fetch_reit_data()
    merge_final_panel()
    print("✅ Milestone 1 complete!")
    print("Run steps available as:")
    print("- python code/fetch_reit_data.py")
    print("- python code/merge_final_panel.py")


if __name__ == "__main__":
    main()