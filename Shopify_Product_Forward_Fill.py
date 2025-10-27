# Imports
import pandas as pd
import tkinter as tk
from tkinter import filedialog, messagebox
from tkinter import ttk
import csv
import re
from html import unescape

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

# Clean Body (HTML) text while keeping readable formatting
import re
from html import unescape

def clean_body_html(df):
    """Convert Shopify Body (HTML) column into readable plain text with basic formatting."""
    if "Body (HTML)" not in df.columns:
        return df

    def clean_text(text):
        if pd.isna(text):
            return ""
        text = str(text).strip()

        # Decode HTML entities (sometimes Shopify double-encodes)
        text = unescape(unescape(text))

        # Replace common HTML formatting tags with readable equivalents
        replacements = {
            r"(?i)<br\s*/?>": "\n",
            r"(?i)</?p>": "\n",
            r"(?i)</?div>": "\n",
            r"(?i)<li>": "• ",
            r"(?i)</li>": "\n",
            r"(?i)</?(ul|ol)>": "\n",
            r"(?i)</?(strong|b|i|em|span)>": "",
        }
        for pattern, replacement in replacements.items():
            text = re.sub(pattern, replacement, text)

        # Remove any remaining HTML tags (but keep text)
        text = re.sub(r"<[^>]+>", "", text)

        # Replace non-breaking spaces and weird characters
        text = text.replace("\xa0", " ").replace("Â", "")

        # Remove stray control characters and excessive whitespace
        text = re.sub(r"[^\x20-\x7E\n]", "", text)  # keep readable ASCII and newlines
        text = re.sub(r"\s+\n", "\n", text)
        text = re.sub(r"\n{3,}", "\n\n", text)

        return text.strip()

    # Apply cleaning
    df["Body (HTML)"] = df["Body (HTML)"].astype(str).apply(clean_text)
    return df

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

    # Clean Body (HTML)
    df = clean_body_html(df)

    # Create Full Title
    df = create_full_title(df)

    # Remove completely empty columns
    df = df.dropna(axis=1, how="all")

    # Convert all data to string to avoid NaN representations
    df = df.astype(str)

    # Replace various NaN-like and blank entries with "N/A"
    df = df.replace(
        {
            "nan": "N/A",
            "NaN": "N/A",
            "None": "N/A",
            "": "N/A",
        }
    )
    df = df.replace(r"^\s+$", "N/A", regex=True)

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

    # Save with all fields quoted and UTF-8 encoding
    df.to_csv(file_path, index=False, encoding="utf-8-sig", quoting=csv.QUOTE_ALL)

    messagebox.showinfo("Saved", f"File saved to:\n{file_path}")

# GUI Setup
app = tk.Tk()
app.title("Shopify CSV Product Forward-Fill & Cleaner")
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
