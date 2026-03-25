#!/usr/bin/env python3
"""
Build a standalone HTML page for GitHub Pages deployment.

All interactivity uses client-side CustomJS callbacks (no Python server needed).
Outputs to docs/index.html.

Usage: python build.py
"""
import os
from os.path import dirname, join

from bokeh.palettes import Turbo256, Category10_10
from bokeh.models import (
    ColumnDataSource, Select, MultiChoice, Div, TabPanel, Tabs,
    Button, CustomJS, CheckboxGroup, RangeSlider,
)
from bokeh.layouts import row, column
from bokeh.resources import CDN
from bokeh.embed import components

import pandas as pd
import plot_tools

SCRIPT_DIR = dirname(os.path.abspath(__file__))
DATA_DIR = join(SCRIPT_DIR, "data")
OUT_DIR = join(SCRIPT_DIR, "docs")

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
black_spec_mat = pd.read_csv(
    join(DATA_DIR, "Specular_Reflect_Data", "Specular_material.csv")
).set_index("Angle (Deg)")

INITIAL_INTENSITY = 10.4629235
black_spec_mat = black_spec_mat / INITIAL_INTENSITY

black_spec_ref_ds = ColumnDataSource(black_spec_mat)
black_spec_ratio_ds = ColumnDataSource(
    pd.read_csv(join(DATA_DIR, "Specular_Reflect_Data", "Spec_Ratio.csv")).set_index("Angle (Deg)")
)
black_tot_ds = ColumnDataSource(
    pd.read_csv(join(DATA_DIR, "Total_Reflect_Data", "Black_Materials_total_reflecatance.csv")).set_index("nm")
)
white_tot_ds = ColumnDataSource(
    pd.read_csv(join(DATA_DIR, "Total_Reflect_Data", "SPIE18_white_all.csv")).set_index("nm")
)
white_lamb_pow_ds = ColumnDataSource(
    pd.read_csv(join(DATA_DIR, "Lambertian_Reflect_Data", "Lamb_Reflect_Power.csv")).set_index("Angle (Deg)")
)
white_lamb_scaled_ds = ColumnDataSource(
    pd.read_csv(join(DATA_DIR, "Lambertian_Reflect_Data", "Lamb_Reflect_Scaled.csv")).set_index("Angle (Deg)")
)
white_lamb_res_ds = ColumnDataSource(
    pd.read_csv(join(DATA_DIR, "Lambertian_Reflect_Data", "Lamb_Resid.csv")).set_index("Angle (Deg)")
)

# ---------------------------------------------------------------------------
# Figures
# ---------------------------------------------------------------------------
total_fig = plot_tools.make_plot("Wavelength (nm)", "Total Reflectance (%)", "Total Reflectance vs Wavelength")
total_fig.x_range.start = 250
total_fig.x_range.end = 2500
total_fig.height = 380

spec_fig = plot_tools.make_plot("Angle (degrees)", "Specular Reflectance", "Specular Reflectance vs Angle")
spec_fig.height = 350

lamb_fig = plot_tools.make_plot("Angle (degrees)", "Power (uW)", "Lambertian Reflectance vs Angle")
lamb_fig.height = 380

lamb_resid_fig = plot_tools.make_plot("Angle (degrees)", "Residual", "Lambertian Residual vs Angle")
lamb_resid_fig.height = 380

# Link lambertian x-ranges so they pan/zoom together
lamb_resid_fig.x_range = lamb_fig.x_range

# Add spectral band annotations to total reflectance
plot_tools.add_spectral_bands(total_fig)

# ---------------------------------------------------------------------------
# Palettes
# ---------------------------------------------------------------------------
n_black_cols = len([c for c in black_tot_ds.data if c != "nm"])
n_white_cols = len([c for c in white_tot_ds.data if c != "nm"])
n_total = n_black_cols + n_white_cols

total_palette = [Turbo256[int(i * 255 / max(n_total - 1, 1))] for i in range(n_total)]
black_palette = total_palette[:n_black_cols]
white_palette = total_palette[n_black_cols:]
spec_palette = Category10_10
lamb_palette = Category10_10

# ---------------------------------------------------------------------------
# Renderers
# ---------------------------------------------------------------------------
black_tot_renderers = plot_tools.plot_lines(
    black_tot_ds, total_fig, "nm", black_palette, False, ["black_tot"]
)
white_tot_renderers = plot_tools.plot_lines(
    white_tot_ds, total_fig, "nm", white_palette, False, ["white_tot"]
)
black_spec_ref_renderers = plot_tools.plot_lines(
    black_spec_ref_ds, spec_fig, "Angle (Deg)", spec_palette, False, ["black_spec"]
)
black_spec_ratio_renderers = plot_tools.plot_lines(
    black_spec_ratio_ds, spec_fig, "Angle (Deg)", spec_palette, False, ["black_ref"]
)
white_lamb_renderers = plot_tools.plot_lines(
    white_lamb_scaled_ds, lamb_fig, "Angle (Deg)", lamb_palette, False, ["white_lamb"]
)
white_lamb_pow_renderers = plot_tools.plot_lines(
    white_lamb_pow_ds, lamb_fig, "Angle (Deg)", lamb_palette, False, ["white_lamb"],
    line_dash="dotdash",
)
white_lamb_resid_renderers = plot_tools.plot_lines(
    white_lamb_res_ds, lamb_resid_fig, "Angle (Deg)", lamb_palette, False, ["white_res"],
    line_dash="dotdash",
)

all_black_renderers = black_tot_renderers + black_spec_ref_renderers
all_white_renderers = (
    white_tot_renderers + white_lamb_renderers
    + white_lamb_pow_renderers + white_lamb_resid_renderers
)
all_renderers = (
    black_tot_renderers + white_tot_renderers
    + black_spec_ref_renderers + black_spec_ratio_renderers
    + white_lamb_renderers + white_lamb_pow_renderers
    + white_lamb_resid_renderers
)

# ---------------------------------------------------------------------------
# "No Data" labels & hover tools
# ---------------------------------------------------------------------------
tot_fig_label = plot_tools.make_label(total_fig, True)
spec_fig_label = plot_tools.make_label(spec_fig, True)
lamb_fig_label = plot_tools.make_label(lamb_fig, True)

total_fig.add_layout(tot_fig_label)
spec_fig.add_layout(spec_fig_label)
lamb_fig.add_layout(lamb_fig_label)
lamb_resid_fig.add_layout(lamb_fig_label)

total_fig.add_tools(plot_tools.make_hovertool("nm", "nm", "Reflectance"))
spec_fig.add_tools(plot_tools.make_hovertool("{Angle (Deg)}", "Angle", "Reflectance"))
lamb_fig.add_tools(plot_tools.make_hovertool("{Angle (Deg)}", "Angle", "Power"))
lamb_resid_fig.add_tools(plot_tools.make_hovertool("{Angle (Deg)}", "Angle", "Residual"))

# ---------------------------------------------------------------------------
# Multi-choice options
# ---------------------------------------------------------------------------
seen = set()
multi_choice_options = []
for rnd in all_renderers:
    if rnd.name not in seen:
        seen.add(rnd.name)
        multi_choice_options.append(rnd.name)

# ---------------------------------------------------------------------------
# Stats display (updated via CustomJS)
# ---------------------------------------------------------------------------
stats_div = Div(
    text="""<div style="color:#888; font-style:italic; padding:8px;">
    Select materials to see live statistics</div>""",
    sizing_mode="stretch_width",
)

# ---------------------------------------------------------------------------
# Checkbox groups for selective download
# ---------------------------------------------------------------------------
checkbox_groups = []

btk_text = Div(text="<b style='color:#00d2ff'>Black Total Data:</b>")
checkbox_groups.append(CheckboxGroup(labels=black_tot_ds.column_names[1:], width=215))

wtk_text = Div(text="<b style='color:#00d2ff'>White Total Data:</b>")
checkbox_groups.append(CheckboxGroup(labels=white_tot_ds.column_names[1:]))

bsk_text = Div(text="<b style='color:#00d2ff'>Black Specular Data:</b>")
checkbox_groups.append(CheckboxGroup(labels=black_spec_ref_ds.column_names[1:], width=125))

bsrk_text = Div(text="<b style='color:#00d2ff'>Black Specular Ratio:</b>")
checkbox_groups.append(CheckboxGroup(labels=black_spec_ratio_ds.column_names[1:], width=125))

wls_text = Div(text="<b style='color:#00d2ff'>White Lambertian Scaled:</b>")
checkbox_groups.append(CheckboxGroup(labels=white_lamb_scaled_ds.column_names[1:], width=125))

wlss_text = Div(text="<b style='color:#00d2ff'>White Lambertian Power:</b>")
checkbox_groups.append(CheckboxGroup(labels=white_lamb_pow_ds.column_names[1:], width=125))

wrs_text = Div(text="<b style='color:#00d2ff'>White Lambertian Residual:</b>")
checkbox_groups.append(CheckboxGroup(labels=white_lamb_res_ds.column_names[1:], width=125))

# ---------------------------------------------------------------------------
# Widgets
# ---------------------------------------------------------------------------
multi_choice = MultiChoice(
    title="Show/Hide Materials",
    options=multi_choice_options,
    placeholder="Type or select materials...",
)

mat_color_select = Select(
    title="Filter Material Color",
    options=["Select Material", "Black", "White", "All"],
    value="Select Material",
)

spec_select = Select(
    title="Specular Variable Type",
    options=["Reflectance", "Ratio"],
)

tot_slider = RangeSlider(start=250, end=2500, value=(250, 2500), step=1,
                         title="Total Reflectance Wavelength Range (nm)")
spec_slider = RangeSlider(start=10, end=160, value=(10, 160), step=1,
                          title="Specular Reflectance Angle Range")
lamb_slider = RangeSlider(start=10, end=90, value=(10, 90), step=1,
                          title="Lambertian Reflectance Angle Range")

totb_button = Button(label="Black Total Reflectance", button_type="success")
totw_button = Button(label="White Total Reflectance", button_type="success")
spec_button = Button(label="Specular Reflectance", button_type="success")
spec_rat_button = Button(label="Specular Ratio", button_type="success")
lamb_button = Button(label="Lambertian Reflectance", button_type="success")
resid_button = Button(label="Lambertian Residual", button_type="success")
selec_button = Button(label="Download Selected Materials", button_type="primary")

# ---------------------------------------------------------------------------
# Shared JS: update statistics panel
# ---------------------------------------------------------------------------
UPDATE_STATS_JS = """
function updateStats(all_renderers, stats_div) {
    let visible_names = [];
    let total_count = 0;
    let black_count = 0;
    let white_count = 0;
    const seen = new Set();
    for (const r of all_renderers) {
        if (r.visible && !seen.has(r.name)) {
            seen.add(r.name);
            visible_names.push(r.name);
            total_count++;
            const tags = r.tags || [];
            if (tags.some(t => t.startsWith('black'))) black_count++;
            else white_count++;
        }
    }
    if (total_count === 0) {
        stats_div.text = '<div style="color:#888; font-style:italic; padding:8px;">Select materials to see live statistics</div>';
        return;
    }
    const names_html = visible_names.slice(0, 12).map(n =>
        '<span style="background:#2a2a4a; padding:2px 8px; border-radius:10px; margin:2px; display:inline-block; font-size:11px;">' + n + '</span>'
    ).join('');
    const more = total_count > 12 ? '<span style="color:#888; font-size:11px;"> +' + (total_count - 12) + ' more</span>' : '';
    stats_div.text = '<div style="padding:8px;">'
        + '<div style="display:flex; gap:20px; margin-bottom:8px;">'
        + '<div><span style="color:#00d2ff; font-size:24px; font-weight:700;">' + total_count + '</span> <span style="color:#888; font-size:12px;">materials visible</span></div>'
        + '<div><span style="color:#e74c3c; font-size:18px; font-weight:600;">' + black_count + '</span> <span style="color:#888; font-size:12px;">black</span></div>'
        + '<div><span style="color:#2ecc71; font-size:18px; font-weight:600;">' + white_count + '</span> <span style="color:#888; font-size:12px;">white</span></div>'
        + '</div>'
        + '<div>' + names_html + more + '</div>'
        + '</div>';
}
"""

# ---------------------------------------------------------------------------
# CustomJS callbacks
# ---------------------------------------------------------------------------
mat_color_js = CustomJS(
    args=dict(
        all_renderers=all_renderers,
        black_renderers=all_black_renderers,
        white_renderers=all_white_renderers,
        tot_label=tot_fig_label,
        spec_label=spec_fig_label,
        lamb_label=lamb_fig_label,
        spec_select=spec_select,
        stats_div=stats_div,
    ),
    code=UPDATE_STATS_JS + """
    const val = cb_obj.value;
    if (val === 'Select Material') {
        for (const r of all_renderers) r.visible = false;
        tot_label.visible = true;
        spec_label.visible = true;
        lamb_label.visible = true;
        spec_select.disabled = true;
    } else if (val === 'All') {
        for (const r of all_renderers) r.visible = true;
        tot_label.visible = false;
        spec_label.visible = false;
        lamb_label.visible = false;
        spec_select.disabled = false;
    } else {
        const is_white = val === 'White';
        for (const r of black_renderers) r.visible = !is_white;
        for (const r of white_renderers) r.visible = is_white;
        spec_select.disabled = is_white;
        spec_label.visible = is_white;
        tot_label.visible = false;
        lamb_label.visible = !is_white;
    }
    updateStats(all_renderers, stats_div);
    """,
)
mat_color_select.js_on_change("value", mat_color_js)

spec_type_js = CustomJS(
    args=dict(
        ratio_renderers=black_spec_ratio_renderers,
        ref_renderers=black_spec_ref_renderers,
        spec_yaxis=spec_fig.yaxis[0],
    ),
    code="""
    const is_ratio = cb_obj.value === 'Ratio';
    spec_yaxis.axis_label = is_ratio ? 'Specular Ratio (%)' : 'Specular Reflectance';
    for (const r of ratio_renderers) r.visible = is_ratio;
    for (const r of ref_renderers) r.visible = !is_ratio;
    """,
)
spec_select.js_on_change("value", spec_type_js)

multi_choice_js = CustomJS(
    args=dict(
        all_renderers=all_renderers,
        multi_choice=multi_choice,
        tot_renderers=black_tot_renderers + white_tot_renderers,
        spec_renderers=black_spec_ref_renderers,
        lamb_renderers=white_lamb_renderers,
        tot_label=tot_fig_label,
        spec_label=spec_fig_label,
        lamb_label=lamb_fig_label,
        stats_div=stats_div,
    ),
    code=UPDATE_STATS_JS + """
    const selected = new Set(multi_choice.value);
    for (const r of all_renderers) {
        r.visible = selected.has(r.name);
    }
    function noData(renderers) {
        for (const r of renderers) { if (r.visible) return false; }
        return true;
    }
    tot_label.visible = noData(tot_renderers);
    spec_label.visible = noData(spec_renderers);
    lamb_label.visible = noData(lamb_renderers);
    updateStats(all_renderers, stats_div);
    """,
)
multi_choice.js_on_change("value", multi_choice_js)

for slider, fig_range in [
    (tot_slider, total_fig.x_range),
    (spec_slider, spec_fig.x_range),
    (lamb_slider, lamb_fig.x_range),
]:
    slider.js_on_change("value", CustomJS(
        args=dict(x_range=fig_range),
        code="x_range.start = cb_obj.value[0]; x_range.end = cb_obj.value[1];",
    ))

# --- Download buttons ---
DOWNLOAD_JS = """
function dataToCsv(source) {
    const columns = Object.keys(source.data);
    const nrows = source.get_length();
    const lines = [columns.join(",")];
    for (let i = 0; i < nrows; i++) {
        const row = [];
        for (const col of columns) row.push(source.data[col][i]);
        lines.push(row.join(","));
    }
    return lines.join("\\n") + "\\n";
}
const blob = new Blob([dataToCsv(source)], {type: "text/csv;charset=utf-8;"});
const link = document.createElement("a");
link.href = URL.createObjectURL(blob);
link.download = filename;
link.style.display = "none";
document.body.appendChild(link);
link.click();
document.body.removeChild(link);
"""

SELEC_DOWNLOAD_JS = """
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
} else {
    const lines = [columns.join(",")];
    const nrows = rnds[rndIndices[0]].data_source.get_length();
    for (let i = 0; i < nrows; i++) {
        const row = [];
        for (const ri of rndIndices) {
            const r = rnds[ri];
            const v = r.data_source.data[r.name][i];
            row.push(v != null && v > -1 ? v : "");
        }
        lines.push(row.join(","));
    }
    const blob = new Blob([lines.join("\\n") + "\\n"], {type: "text/csv;charset=utf-8;"});
    const link = document.createElement("a");
    link.href = URL.createObjectURL(blob);
    link.download = "selected_materials.csv";
    link.style.display = "none";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
"""

for btn, ds, fname in [
    (totb_button, black_tot_ds, "black_total_reflectance.csv"),
    (totw_button, white_tot_ds, "white_total_reflectance.csv"),
    (spec_button, black_spec_ref_ds, "specular_reflectance.csv"),
    (spec_rat_button, black_spec_ratio_ds, "specular_ratio.csv"),
    (lamb_button, white_lamb_scaled_ds, "lambertian_reflectance.csv"),
    (resid_button, white_lamb_res_ds, "lambertian_residual.csv"),
]:
    btn.js_on_click(CustomJS(args=dict(source=ds, filename=fname), code=DOWNLOAD_JS))

selec_button.js_on_click(
    CustomJS(args=dict(groups=checkbox_groups, rnds=all_renderers), code=SELEC_DOWNLOAD_JS)
)

# ---------------------------------------------------------------------------
# Layout
# ---------------------------------------------------------------------------
instructions = Div(text="""
<div style="line-height:1.6;">
<p style="font-size:15px; margin-top:0;">Interactive visualization of optical reflectance data for black and white materials.
Use the tabs to filter, adjust ranges, or download data.</p>
<div style="display:grid; grid-template-columns:repeat(auto-fit, minmax(200px, 1fr)); gap:12px; margin-top:12px;">
  <div style="background:rgba(0,210,255,0.05); border:1px solid rgba(0,210,255,0.15); border-radius:8px; padding:12px;">
    <div style="font-weight:600; color:#00d2ff; margin-bottom:4px;">Filters</div>
    <div style="font-size:13px; color:#aaa;">Filter by material color or search for specific materials by name.</div>
  </div>
  <div style="background:rgba(46,204,113,0.05); border:1px solid rgba(46,204,113,0.15); border-radius:8px; padding:12px;">
    <div style="font-weight:600; color:#2ecc71; margin-bottom:4px;">Range Sliders</div>
    <div style="font-size:13px; color:#aaa;">Narrow the wavelength or angle range on each plot.</div>
  </div>
  <div style="background:rgba(155,89,182,0.05); border:1px solid rgba(155,89,182,0.15); border-radius:8px; padding:12px;">
    <div style="font-weight:600; color:#9b59b6; margin-bottom:4px;">Downloads</div>
    <div style="font-size:13px; color:#aaa;">Export full datasets or selected materials as CSV.</div>
  </div>
  <div style="background:rgba(231,76,60,0.05); border:1px solid rgba(231,76,60,0.15); border-radius:8px; padding:12px;">
    <div style="font-weight:600; color:#e74c3c; margin-bottom:4px;">Plot Tools</div>
    <div style="font-size:13px; color:#aaa;">Box zoom, pan, wheel zoom, crosshair, and hover tooltips.</div>
  </div>
</div>
</div>
""")

band_legend = Div(text="""
<div style="display:flex; gap:16px; align-items:center; padding:4px 0; font-size:12px; color:#888;">
  <span style="font-weight:600; color:#aaa;">Spectral Bands:</span>
  <span><span style="display:inline-block;width:12px;height:12px;background:#9b59b6;border-radius:2px;opacity:0.5;vertical-align:middle;margin-right:4px;"></span>UV (250-400nm)</span>
  <span><span style="display:inline-block;width:12px;height:12px;background:#2ecc71;border-radius:2px;opacity:0.5;vertical-align:middle;margin-right:4px;"></span>Visible (400-700nm)</span>
  <span><span style="display:inline-block;width:12px;height:12px;background:#e74c3c;border-radius:2px;opacity:0.5;vertical-align:middle;margin-right:4px;"></span>NIR (700-2500nm)</span>
</div>
""", sizing_mode="stretch_width")

filter_layout = row(mat_color_select, spec_select, multi_choice, sizing_mode="stretch_width")
slider_layout = column(tot_slider, spec_slider, lamb_slider, sizing_mode="stretch_width")

download_header = Div(text="<p style='color:#aaa; font-size:13px; margin:0 0 8px 0;'>Select individual materials below, then click <b>Download Selected Materials</b>.</p>")
download_select_layout = column(
    download_header,
    row(
        column(btk_text, checkbox_groups[0]),
        column(wtk_text, checkbox_groups[1]),
        column(bsk_text, checkbox_groups[2], bsrk_text, checkbox_groups[3]),
        column(wls_text, checkbox_groups[4], wlss_text, checkbox_groups[5]),
        column(wrs_text, checkbox_groups[6]),
        sizing_mode="stretch_width",
    ),
    sizing_mode="stretch_width",
)

download_header2 = Div(text="<p style='color:#aaa; font-size:13px; margin:0 0 8px 0;'>Download complete datasets by category, or download your selected materials.</p>")
download_buttons_layout = column(
    download_header2,
    row(
        column(totb_button, totw_button),
        column(spec_button, spec_rat_button),
        column(lamb_button, resid_button),
    ),
    selec_button,
)

tabs = Tabs(tabs=[
    TabPanel(child=instructions, title="Overview"),
    TabPanel(child=filter_layout, title="Filters"),
    TabPanel(child=slider_layout, title="Range Sliders"),
    TabPanel(child=download_select_layout, title="Select Data"),
    TabPanel(child=download_buttons_layout, title="Downloads"),
], active=0)

page_layout = column(
    tabs,
    stats_div,
    band_legend,
    total_fig,
    spec_fig,
    row(lamb_fig, lamb_resid_fig, sizing_mode="stretch_width"),
    sizing_mode="stretch_width",
)

# ---------------------------------------------------------------------------
# Generate HTML
# ---------------------------------------------------------------------------
PAGE_CSS = """
*{box-sizing:border-box;margin:0;padding:0}
html{scroll-behavior:smooth}
body{
    font-family:-apple-system,BlinkMacSystemFont,"Segoe UI",Roboto,Helvetica,Arial,sans-serif;
    background:#0a0a1a;
    color:#e0e0e0;
    min-height:100vh;
}

/* Animated gradient header */
.hero{
    background:linear-gradient(135deg,#500000 0%,#1a1a2e 40%,#16213e 70%,#0f3460 100%);
    background-size:200% 200%;
    animation:gradientShift 8s ease infinite;
    padding:32px 24px 28px;
    border-bottom:1px solid rgba(255,255,255,0.05);
}
@keyframes gradientShift{
    0%{background-position:0% 50%}
    50%{background-position:100% 50%}
    100%{background-position:0% 50%}
}
.hero-inner{
    max-width:1200px;margin:0 auto;
    display:flex;align-items:center;justify-content:space-between;
    flex-wrap:wrap;gap:16px;
}
.hero h1{
    font-size:28px;font-weight:800;letter-spacing:-0.5px;
    background:linear-gradient(135deg,#ffffff 0%,#00d2ff 100%);
    -webkit-background-clip:text;-webkit-text-fill-color:transparent;
    background-clip:text;
}
.hero .subtitle{
    font-size:14px;color:rgba(255,255,255,0.5);margin-top:4px;
}
.nav-links{display:flex;gap:12px;align-items:center;}
.nav-links a{
    color:rgba(255,255,255,0.7);text-decoration:none;font-size:13px;
    padding:6px 14px;border-radius:6px;
    border:1px solid rgba(255,255,255,0.1);
    transition:all 0.2s;
}
.nav-links a:hover{
    color:#fff;border-color:rgba(0,210,255,0.4);
    background:rgba(0,210,255,0.08);
}

/* Main container */
.main{max-width:1200px;margin:0 auto;padding:20px 16px 60px;}

/* Glass cards */
.glass-card{
    background:rgba(26,26,46,0.6);
    backdrop-filter:blur(12px);-webkit-backdrop-filter:blur(12px);
    border:1px solid rgba(255,255,255,0.06);
    border-radius:12px;
    padding:20px;
    margin-bottom:20px;
    transition:border-color 0.3s;
}
.glass-card:hover{border-color:rgba(0,210,255,0.15);}

.plot-grid{
    display:grid;gap:20px;margin-bottom:20px;
}
.plot-grid.full{grid-template-columns:1fr;}
.plot-grid.half{grid-template-columns:1fr 1fr;}
@media(max-width:900px){.plot-grid.half{grid-template-columns:1fr;}}

.plot-card{
    background:rgba(22,33,62,0.5);
    border:1px solid rgba(255,255,255,0.04);
    border-radius:12px;
    padding:12px;
    overflow:hidden;
    transition:transform 0.2s,border-color 0.3s;
}
.plot-card:hover{
    border-color:rgba(0,210,255,0.2);
    transform:translateY(-2px);
}

/* Section labels */
.section-label{
    display:flex;align-items:center;gap:8px;
    margin-bottom:12px;font-size:11px;text-transform:uppercase;
    letter-spacing:1.5px;color:#555577;font-weight:600;
}
.section-label::after{
    content:'';flex:1;height:1px;
    background:linear-gradient(90deg,rgba(0,210,255,0.2),transparent);
}

/* Footer */
.footer{
    text-align:center;padding:32px 16px;
    color:#333355;font-size:12px;
    border-top:1px solid rgba(255,255,255,0.03);
}
.footer a{color:#555577;text-decoration:none;}
.footer a:hover{color:#00d2ff;}

/* Button overrides */
.bk-btn-success{
    color:#fff!important;background:#26a69a!important;border:none!important;
    border-radius:6px!important;padding:8px 18px!important;cursor:pointer;
    transition:all 0.2s!important;font-size:13px!important;margin:4px 0!important;
}
.bk-btn-success:hover{background:#2bbbad!important;transform:translateY(-1px);}
.bk-btn-primary{
    color:#fff!important;background:linear-gradient(135deg,#500000,#0f3460)!important;
    border:none!important;border-radius:6px!important;padding:10px 24px!important;
    cursor:pointer;transition:all 0.2s!important;font-size:14px!important;
    font-weight:600!important;margin:8px 0!important;
}
.bk-btn-primary:hover{opacity:0.9;transform:translateY(-1px);}

/* Bokeh widget overrides for dark theme */
.bk-input{
    background:#1a1a2e!important;color:#e0e0e0!important;
    border-color:#2a2a4a!important;border-radius:6px!important;
}
.bk-input:focus{border-color:#00d2ff!important;}
select.bk-input{background:#1a1a2e!important;}
.bk-tab{
    background:#16213e!important;color:#888!important;
    border:1px solid rgba(255,255,255,0.06)!important;
    border-radius:8px 8px 0 0!important;padding:8px 16px!important;
    transition:all 0.2s!important;
}
.bk-tab:hover{color:#ccc!important;}
.bk-tab.bk-active{
    background:#1a1a2e!important;color:#00d2ff!important;
    border-bottom-color:#1a1a2e!important;
}
.bk-headers{border-bottom:1px solid rgba(255,255,255,0.06)!important;}
.bk-slider-title{color:#aaa!important;}
.noUi-connect{background:#00d2ff!important;}
.noUi-handle{background:#16213e!important;border-color:#00d2ff!important;}
label.bk{color:#ccc!important;}

/* Scrollbar */
::-webkit-scrollbar{width:8px;height:8px;}
::-webkit-scrollbar-track{background:#0a0a1a;}
::-webkit-scrollbar-thumb{background:#2a2a4a;border-radius:4px;}
::-webkit-scrollbar-thumb:hover{background:#3a3a5a;}
"""

PAGE_TEMPLATE = """\
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{{ title }}</title>
    {{ bokeh_css }}
    {{ bokeh_js }}
    <style>{{ page_css }}</style>
</head>
<body>
    <header class="hero">
        <div class="hero-inner">
            <div>
                <h1>Black &amp; White Materials Reflectance</h1>
                <div class="subtitle">Texas A&amp;M Instrumentation Lab &mdash; Interactive Data Explorer</div>
            </div>
            <div class="nav-links">
                <a href="https://instrumentation.tamu.edu/">Lab Home</a>
                <a href="https://github.com/matthewholden01/reflectance-plots">GitHub</a>
            </div>
        </div>
    </header>

    <div class="main">
        <div class="glass-card">
            {{ plot_div }}
        </div>
    </div>

    <footer class="footer">
        Texas A&amp;M University &mdash; Instrumentation Lab
        &nbsp;&bull;&nbsp;
        <a href="https://github.com/matthewholden01/reflectance-plots">Source Code</a>
    </footer>
    {{ plot_script }}
</body>
</html>
"""

from jinja2 import Template

script, div = components(page_layout)
template = Template(PAGE_TEMPLATE)
final_html = template.render(
    title="B/W Materials Reflectance Data",
    bokeh_css=CDN.render_css(),
    bokeh_js=CDN.render_js(),
    page_css=PAGE_CSS,
    plot_div=div,
    plot_script=script,
)

os.makedirs(OUT_DIR, exist_ok=True)
out_path = join(OUT_DIR, "index.html")
with open(out_path, "w") as f:
    f.write(final_html)

print(f"Built standalone page: {out_path}")
print(f"File size: {os.path.getsize(out_path) / 1024 / 1024:.1f} MB")
