function dataToCsv(source) {
    const columns = Object.keys(source.data);
    const nrows = source.get_length();
    const lines = [columns.join(",")];

    for (let i = 0; i < nrows; i++) {
        const row = [];
        for (const col of columns) {
            row.push(source.data[col][i]);
        }
        lines.push(row.join(","));
    }
    return lines.join("\n") + "\n";
}

const filename = "reflectance_data.csv";
const filetext = dataToCsv(source);
const blob = new Blob([filetext], { type: "text/csv;charset=utf-8;" });
const link = document.createElement("a");
link.href = URL.createObjectURL(blob);
link.download = filename;
link.style.display = "none";
document.body.appendChild(link);
link.click();
document.body.removeChild(link);
