# Shopify Product CSV File Forward Fill

A simple Python GUI application to clean and forward-fill Shopify product CSV files. For a proper demo, visit the **"Releases"** tab and open the "demo_app.zip" file (there is both a Windows and Mac version).

---
## What is Forward-Filling?

**Forward-filling** is a method for filling missing values in a dataset by **carrying the last known value forward** to replace empty cells.  
If a value is missing, forward-filling replaces it with the most recent non-missing value above it.

---
## Forward-Fill Example

| Handle  | Title       | Price |
|---------|------------|-------|
| shirt1  | T-Shirt    | 20    |
| shirt1  | *NaN*      | 22    |
| shirt1  | *NaN*      | 24    |

After forward-filling by Handle:

| Handle  | Title       | Price |
|---------|------------|-------|
| shirt1  | T-Shirt    | 20    |
| shirt1  | T-Shirt    | 22    |
| shirt1  | T-Shirt    | 24    |

- Only missing values in the selected columns are filled.  
- Variant-specific data (e.g., `Price`) remains intact.  

---

## Why Forward-Filling?

In Shopify, a single product can have **many variants** (for example, color or size). Each variant appears as a separate row in the CSV file.  

However, descriptive fields like Title, Body (HTML), or Vendor are often only filled in the first variant row, leaving other rows empty:

<img width="937" height="156" alt="Screenshot 2025-10-24 at 6 18 11 PM" src="https://github.com/user-attachments/assets/a9f080a5-2638-44c5-97f7-52ecee8bf723" />

Forward-filling ensures that all variants inherit the correct product information, so your Shopify import is consistent and complete. For further details about how the product csv file is structured, [click here](https://help.shopify.com/en/manual/products/import-export/using-csv)


---

## How the Application Works

1. **Upload Shopify CSV**
   - Export your product CSV file from Shopify (Make sure that the **All Products** option is selected).  
   - Make sure that the required columns `Handle`, `Title`, `Body (HTML)`, `Vendor`, and `Image Src` are included.

2. **Select Columns to Forward-Fill**
   - You can manually adjust selections as needed.
   - Columns are automatically pre-selected based on Shopify's default structure.  
   - Non-empty metafields are also pre-selected by default.  

3. **Forward-Fill by Handle**
   - Forward-fill occurs **within each product (grouped by Handle)**. This ensures data from one product does **not** spill into another.
   - A new field "Full Title" is created, combining the product Title with Option Values 1-3 (2-3 are not required, any Option1 Value with the standard "Default Title" field will not be included )
   - After forward-filling is complete, any remaining empty fields are replaced with "N/A". This is done to make the file easier to read.
     
4. **Save Cleaned CSV**
   - Export the cleaned CSV file to the location of your choosing.

---
