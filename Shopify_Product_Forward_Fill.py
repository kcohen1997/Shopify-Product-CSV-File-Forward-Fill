# Imports
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import csv

# Default Shopify product columns to auto-select for forward-filling
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

# Create Full Title column safely
def create_full_title(df):
    for col in ["Option1 Value", "Option2 Value", "Option3 Value"]:
        if col not in df.columns:
            df[col] = ""
    def combine_row(row):
        parts = []
        for col in ["Title", "Option1 Value", "Option2 Value", "Option3 Value"]:
            val = row.get(col, "")
            if pd.notna(val) and str(val).strip() != "":
                parts.append(str(val))
        return " - ".join(parts)
    if "Full Title" in df.columns:
        df.drop(columns=["Full Title"], inplace=True)
    df.insert(1, "Full Title", df.apply(combine_row, axis=1))
    return df

# Step 1: Upload and verify CSV
def upload_file():
    file_path = filedialog.askopenfilename(
        title="Select Shopify Product CSV",
        filetypes=[("CSV files", "*.csv")]
    )
    if not file_path:
        return
    try:
        df = pd.read_csv(file_path)
        is_valid, missing = is_shopify_csv(df)
        if not is_valid:
            messagebox.showerror(
                "Invalid File",
                f"This file does NOT appear to be a Shopify product export.\nMissing columns: {', '.join(missing)}"
            )
            return
        available_columns = [col for col in df.columns if col not in ["Handle", "Full Title"]]
        preselected_cols = set(DEFAULT_FORWARD_FILL_COLS)
        for col in available_columns:
            if "metafield" in col.lower() and not df[col].isna().all():
                preselected_cols.add(col)
        column_listbox.delete(0, tk.END)
        for col in available_columns:
            column_listbox.insert(tk.END, col)
            if col in preselected_cols:
                column_listbox.selection_set(tk.END)
        app.df = df
    except Exception as e:
        messagebox.showerror("Error", str(e))

# Step 2: Forward-fill selected columns by Handle
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
    df[selected_cols] = df.groupby("Handle")[selected_cols].ffill()
    app.df = df
    messagebox.showinfo(
        "Success",
        f"Forward-filled {len(selected_cols)} columns by Handle"
    )

# Step 3: Save cleaned CSV
def save_file():
    if not hasattr(app, "df"):
        messagebox.showwarning("No Data", "Please process a CSV first.")
        return
    df = app.df.copy()
    # Replace "Default Title" in Option1 Value with blank
    if "Option1 Value" in df.columns:
        df.loc[df["Option1 Value"] == "Default Title", "Option1 Value"] = ""
    # Create Full Title
    df = create_full_title(df)
    # Remove completely empty columns
    df = df.dropna(axis=1, how="all")
    # Fill non-selected columns with "N/A"
    selected_indices = column_listbox.curselection()
    selected_cols = [column_listbox.get(i) for i in selected_indices]
    non_selected_cols = [col for col in df.columns if col not in selected_cols]
    df[non_selected_cols] = df[non_selected_cols].fillna("N/A")
    # Reorder columns: Handle → Full Title → Title → rest
    cols = list(df.columns)
    ordered_cols = ["Handle", "Full Title", "Title"]
    remaining_cols = [c for c in cols if c not in ordered_cols]
    ordered_cols += remaining_cols
    df = df[ordered_cols]
    # Save CSV
    file_path = filedialog.asksaveasfilename(
        defaultextension=".csv",
        filetypes=[("CSV files", "*.csv")],
        title="Save Cleaned Shopify CSV"
    )
    if not file_path:
        return
    df.to_csv(file_path, index=False, encoding='utf-8-sig', quoting=csv.QUOTE_ALL)
    messagebox.showinfo("Saved", f"File saved to:\n{file_path}")

# GUI Setup
app = tk.Tk()
app.title("Shopify CSV Product Forward-Fill")
app.geometry("540x550")

frame = ttk.Frame(app, padding=10)
frame.pack(fill="both", expand=True)

ttk.Label(frame, text="Step 1: Upload Shopify Product CSV").pack(pady=5)
ttk.Button(frame, text="Upload File", command=upload_file).pack(pady=5)

ttk.Label(frame, text="Step 2: Select Columns to Forward-Fill (by Handle)").pack(pady=5)
column_listbox = tk.Listbox(frame, selectmode=tk.MULTIPLE, height=14)
column_listbox.pack(fill="both", expand=True, pady=5)

ttk.Button(frame, text="Step 3: Forward Fill Selected Columns (by Handle)", command=forward_fill_by_handle).pack(pady=10)
ttk.Button(frame, text="Step 4: Save Cleaned CSV", command=save_file).pack(pady=10)

app.mainloop()
