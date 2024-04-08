
def highlight_max_exclude(row):
    row_minus_first_col = row.iloc[1:]  # Exclude the first column
    if row_minus_first_col.sum() == 0:  # Check if all values are 0
        return [''] * len(row)
    else:
        max_index = row_minus_first_col.idxmax()
        return ['background-color: yellow' if i == max_index else '' for i in row.index]