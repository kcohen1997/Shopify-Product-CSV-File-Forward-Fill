# Imports
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import csv

# Default Shopify product columns to auto-select for forward-filling (As of Oct 24, 2025)
DEFAULT_FORWARD_FILL_COLS = {
    "Title",
    "Body (HTML)",
    "Vendor",
    "Product Category",
    "Type",
    "Tags",
    "Published",
    "Option1 Name",
    "Option2 Name",
    "Option3 Name",
    "Gift Card",
    "SEO Title",
    "SEO Description",
    "Google Shopping / Google Product Category",
    "Google Shopping / Gender",
    "Google Shopping / Age Group",
    "Google Shopping / MPN",
    "Google Shopping / Condition",
    "Google Shopping / Custom Product",
    "Included / United States",
    "Price / United States",
    "Compare At Price / United States",
    "Included / International",
    "Price / International",
    "Compare At Price / International",
    "Status",
}

# Validate Shopify CSV by checking for required columns
def is_shopify_csv(df):
    required_columns = {"Handle", "Title", "Body (HTML)", "Vendor", "Image Src"}
    all_cols = set(df.columns)
    missing = required_columns - all_cols
    if missing:
        return False, missing
    return True, None

# *** Step 1: Upload and verify CSV ***
def upload_file():
    file_path = filedialog.askopenfilename(
        title="Select Shopify Product CSV",
        filetypes=[("CSV files", "*.csv")]
    )
    if not file_path:
        return

    try:
        df = pd.read_csv(file_path)

        # Validate Shopify columns
        is_valid, missing = is_shopify_csv(df)
        if not is_valid:
            messagebox.showerror(
                "Invalid File",
                f"This file does NOT appear to be a Shopify product export.\n"
                f"Missing columns: {', '.join(missing)}"
            )
            return

        # Drop completely empty columns
        df = df.dropna(axis=1, how="all")

        # Exclude 'Handle' from selectable columns
        available_columns = [col for col in df.columns if col != "Handle"]

        # Determine columns to auto-select (defaults + non-empty metafields)
        preselected_cols = set()
        preselected_cols |= DEFAULT_FORWARD_FILL_COLS
        for col in available_columns:
            if "metafield" in col.lower() and not df[col].isna().all():
                preselected_cols.add(col)

        # Populate listbox and auto-select columns
        column_listbox.delete(0, tk.END)
        for col in available_columns:
            column_listbox.insert(tk.END, col)
            if col in preselected_cols:
                column_listbox.selection_set(tk.END)

        # Store dataframe in app
        app.df = df

    except Exception as e:
        messagebox.showerror("Error", str(e))


# *** Step 2: Forward-fill selected columns by Handle *** 
# Fill empty cells in non-selected columns with "N/A"
def forward_fill_by_handle():
    if not hasattr(app, "df"):
        messagebox.showwarning("No File", "Please upload a CSV first.")
        return

    selected_indices = column_listbox.curselection()
    if not selected_indices:
        messagebox.showwarning("No Columns", "Please select at least one column to forward-fill.")
        return

    df = app.df.copy()
    selected_cols = [column_listbox.get(i) for i in selected_indices]

    if "Handle" not in df.columns:
        messagebox.showerror("Missing Handle", "The CSV must include a 'Handle' column to group by.")
        return

    # Forward-fill selected columns within each Handle group
    df[selected_cols] = df.groupby("Handle")[selected_cols].ffill()

    # Fill any empty cells in non-selected columns with "N/A"
    non_selected_cols = [col for col in df.columns if col not in selected_cols]
    df[non_selected_cols] = df[non_selected_cols].fillna("N/A")

    app.df = df
    messagebox.showinfo(
        "Success",
        f"Forward-filled {len(selected_cols)} columns by Handle"
    )

# *** Step 3: Save cleaned CSV (Excel-safe) ***
def save_file():
    if not hasattr(app, "df"):
        messagebox.showwarning("No Data", "Please process a CSV first.")
        return

    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        title="Step 4: Save Cleaned Shopify CSV"
    )
    if not file_path:
        return

    # Save CSV with UTF-8 BOM and all fields quoted to preserve Excel alignment
    app.df.to_csv(file_path, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
    messagebox.showinfo("Saved", f"File saved to:\n{file_path}")


# *** GUI Setup ***
app = tk.Tk()
app.title("Shopify CSV Product Forward-Fill")
app.geometry("540x550")

frame = ttk.Frame(app, padding=10)
frame.pack(fill="both", expand=True)

# Upload CSV
ttk.Label(frame, text="Step 1: Upload Shopify Product CSV").pack(pady=5)
ttk.Button(frame, text="Upload File", command=upload_file).pack(pady=5)

# Column selection
ttk.Label(frame, text="Step 2: Select Columns to Forward-Fill (by Handle)").pack(pady=5)
column_listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, height=14)
column_listbox.pack(fill="both", expand=True, pady=5)

# Forward-fill + Save buttons
ttk.Button(frame, text="Step 3: Forward Fill Selected Columns (by Handle)", command=forward_fill_by_handle).pack(pady=10)
ttk.Button(frame, text="Save Cleaned CSV", command=save_file).pack(pady=10)

# Launch GUI
app.mainloop()
