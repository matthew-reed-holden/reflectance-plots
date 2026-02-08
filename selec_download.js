function createSelectedCsv(groups, rnds) {
    const columns = [];
    const rndIndices = [];
    let idx = 0;

    for (const group of groups) {
        for (const activeIdx of group.active) {
            columns.push(group.labels[activeIdx]);
            rndIndices.push(activeIdx + idx);
        }
        idx += group.labels.length;
    }

    if (columns.length === 0) {
        alert("No materials selected. Please select at least one material.");
        return null;
    }

    const lines = [columns.join(",")];

    // Determine row count from the first selected renderer's data
    const firstRnd = rnds[rndIndices[0]];
    const nrows = firstRnd.data_source.get_length();

    for (let i = 0; i < nrows; i++) {
        const row = [];
        for (const rndIdx of rndIndices) {
            const rnd = rnds[rndIdx];
            const val = rnd.data_source.data[rnd.name][i];
            row.push(val != null && val > -1 ? val : "");
        }
        lines.push(row.join(","));
    }
    return lines.join("\n") + "\n";
}

const filetext = createSelectedCsv(groups, rnds);
if (filetext) {
    const filename = "selected_materials.csv";
    const blob = new Blob([filetext], { type: "text/csv;charset=utf-8;" });
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = filename;
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
