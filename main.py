"""
Bokeh server application for visualizing reflectance data of black and white materials.

Displays total reflectance, specular reflectance, and lambertian reflectance
measurements in interactive plots with filtering, range adjustment, and data download.

Launch with: bokeh serve --show reflectance-plots
"""
from os.path import dirname, join

from bokeh.palettes import Turbo256, Category10_10
from bokeh.models import (
    ColumnDataSource, Select, MultiChoice, Div, TabPanel, Tabs,
    Button, CustomJS, CheckboxGroup, RangeSlider,
    DataTable, TableColumn, NumberFormatter, StringFormatter,
)
from bokeh.layouts import row, column
from bokeh.io import curdoc

import pandas as pd
import plot_tools

# ---------------------------------------------------------------------------
# Data loading
# ---------------------------------------------------------------------------
DATA_DIR = join(dirname(__file__), "data")

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

# Link lambertian x-ranges
lamb_resid_fig.x_range = lamb_fig.x_range

# Add spectral band annotations
plot_tools.add_spectral_bands(total_fig)

total_fig.name = "total"
spec_fig.name = "spec"
lamb_fig.name = "lamb"
lamb_resid_fig.name = "resid"

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
# Multi-choice, labels, hover tools
# ---------------------------------------------------------------------------
seen = set()
multi_choice_options = []
for rnd in all_renderers:
    if rnd.name not in seen:
        seen.add(rnd.name)
        multi_choice_options.append(rnd.name)

tot_fig_label = plot_tools.make_label(total_fig, True)
spec_fig_label = plot_tools.make_label(spec_fig, True)
lamb_fig_label = plot_tools.make_label(lamb_fig, True)

total_fig.add_layout(tot_fig_label)
spec_fig.add_layout(spec_fig_label)
lamb_fig.add_layout(lamb_fig_label)
lamb_resid_fig.add_layout(lamb_fig_label)

# Hover-highlight on total reflectance
total_hover = plot_tools.make_hovertool("nm", "nm", "Reflectance")
total_hover.callback = CustomJS(
    args=dict(renderers=black_tot_renderers + white_tot_renderers),
    code="""
    const indices = cb_data.index.indices;
    if (indices.length === 0) {
        for (const r of renderers) { r.glyph.line_width = 1.5; r.glyph.line_alpha = 0.9; }
        return;
    }
    const hovered_name = cb_data.renderer.name;
    for (const r of renderers) {
        if (r.name === hovered_name) { r.glyph.line_width = 3.5; r.glyph.line_alpha = 1.0; }
        else { r.glyph.line_width = 0.8; r.glyph.line_alpha = 0.3; }
    }
    """,
)
total_fig.add_tools(total_hover)
spec_fig.add_tools(plot_tools.make_hovertool("{Angle (Deg)}", "Angle", "Reflectance"))
lamb_fig.add_tools(plot_tools.make_hovertool("{Angle (Deg)}", "Angle", "Power"))
lamb_resid_fig.add_tools(plot_tools.make_hovertool("{Angle (Deg)}", "Angle", "Residual"))

# ---------------------------------------------------------------------------
# Stats display
# ---------------------------------------------------------------------------
stats_div = Div(
    text='<div style="color:#888; font-style:italic; padding:8px;">Select materials to see live statistics</div>',
    name="stats",
    sizing_mode="stretch_width",
)

# ---------------------------------------------------------------------------
# Checkbox groups for download
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
    title="Show/Hide Materials", options=multi_choice_options,
    name="multi", placeholder="Type or select materials...",
)
mat_color_select = Select(
    title="Filter Material Color",
    options=["Select Material", "Black", "White", "All"],
    value="Select Material", name="color",
)
spec_select = Select(title="Specular Variable Type", options=["Reflectance", "Ratio"], name="spec_select")

tot_slider = RangeSlider(start=250, end=2500, value=(250, 2500), step=1,
                         title="Total Reflectance Wavelength Range (nm)")
spec_slider = RangeSlider(start=10, end=160, value=(10, 160), step=1,
                          title="Specular Reflectance Angle Range")
lamb_slider = RangeSlider(start=10, end=90, value=(10, 90), step=1,
                          title="Lambertian Reflectance Angle Range")

# Quick wavelength zoom buttons
uv_btn = Button(label="UV (250-400nm)", button_type="light", width=140)
vis_btn = Button(label="Visible (400-700nm)", button_type="light", width=160)
nir_btn = Button(label="NIR (700-2500nm)", button_type="light", width=160)
full_btn = Button(label="Full Range", button_type="light", width=120)

for btn, lo, hi in [(uv_btn, 250, 400), (vis_btn, 400, 700), (nir_btn, 700, 2500), (full_btn, 250, 2500)]:
    btn.js_on_click(CustomJS(
        args=dict(x_range=total_fig.x_range, slider=tot_slider, lo=lo, hi=hi),
        code="x_range.start = lo; x_range.end = hi; slider.value = [lo, hi];",
    ))

# Data summary table
table_source = ColumnDataSource(data=dict(
    name=[], category=[], min_val=[], max_val=[], mean_val=[],
))
summary_table = DataTable(
    source=table_source,
    columns=[
        TableColumn(field="name", title="Material", width=150,
                    formatter=StringFormatter(font_style="bold")),
        TableColumn(field="category", title="Type", width=80),
        TableColumn(field="min_val", title="Min", width=90,
                    formatter=NumberFormatter(format="0.4f")),
        TableColumn(field="max_val", title="Max", width=90,
                    formatter=NumberFormatter(format="0.4f")),
        TableColumn(field="mean_val", title="Mean", width=90,
                    formatter=NumberFormatter(format="0.4f")),
    ],
    width=550, height=200, index_position=None,
    sizing_mode="stretch_width", name="summary_table",
)

totb_button = Button(label="Black Total Reflectance", button_type="success")
totw_button = Button(label="White Total Reflectance", button_type="success")
spec_button = Button(label="Specular Reflectance", button_type="success")
spec_rat_button = Button(label="Specular Ratio", button_type="success")
lamb_button = Button(label="Lambertian Reflectance", button_type="success")
resid_button = Button(label="Lambertian Residual", button_type="success")
selec_button = Button(label="Download Selected Materials", button_type="primary")

# ---------------------------------------------------------------------------
# Python callbacks
# ---------------------------------------------------------------------------
def _update_stats():
    import math
    visible = []
    black_n = white_n = 0
    seen_names = set()
    names_list, cats, mins, maxs, means = [], [], [], [], []
    for r in all_renderers:
        if r.visible and r.name not in seen_names:
            seen_names.add(r.name)
            visible.append(r.name)
            tags = r.tags or []
            is_black = any(t.startswith("black") for t in tags)
            if is_black:
                black_n += 1
            else:
                white_n += 1
            # Compute stats from data source
            data = r.data_source.data.get(r.name, [])
            vals = [v for v in data if v is not None and math.isfinite(v)]
            if vals:
                names_list.append(r.name)
                cats.append("Black" if is_black else "White")
                mins.append(min(vals))
                maxs.append(max(vals))
                means.append(sum(vals) / len(vals))
    table_source.data = dict(name=names_list, category=cats, min_val=mins, max_val=maxs, mean_val=means)
    total = len(visible)
    if total == 0:
        stats_div.text = '<div style="color:#888; font-style:italic; padding:8px;">Select materials to see live statistics</div>'
        return
    names_html = " ".join(
        f'<span style="background:#2a2a4a;padding:2px 8px;border-radius:10px;margin:2px;display:inline-block;font-size:11px;">{n}</span>'
        for n in visible[:12]
    )
    more = f'<span style="color:#888;font-size:11px;"> +{total - 12} more</span>' if total > 12 else ""
    stats_div.text = (
        f'<div style="padding:8px;">'
        f'<div style="display:flex;gap:20px;margin-bottom:8px;">'
        f'<div><span style="color:#00d2ff;font-size:24px;font-weight:700;">{total}</span> <span style="color:#888;font-size:12px;">materials visible</span></div>'
        f'<div><span style="color:#e74c3c;font-size:18px;font-weight:600;">{black_n}</span> <span style="color:#888;font-size:12px;">black</span></div>'
        f'<div><span style="color:#2ecc71;font-size:18px;font-weight:600;">{white_n}</span> <span style="color:#888;font-size:12px;">white</span></div>'
        f'</div><div>{names_html}{more}</div></div>'
    )


def check_for_data(renderers):
    return not any(r.visible for r in renderers)


def update_mat_color(attr, old, new):
    if new == "Select Material":
        for r in all_renderers:
            r.visible = False
        tot_fig_label.visible = spec_fig_label.visible = lamb_fig_label.visible = True
        spec_select.disabled = True
    elif new == "All":
        for r in all_renderers:
            r.visible = True
        tot_fig_label.visible = spec_fig_label.visible = lamb_fig_label.visible = False
        spec_select.disabled = False
    else:
        is_white = new == "White"
        for r in all_black_renderers:
            r.visible = not is_white
        for r in all_white_renderers:
            r.visible = is_white
        spec_select.disabled = is_white
        spec_fig_label.visible = is_white
        tot_fig_label.visible = False
        lamb_fig_label.visible = not is_white
    _update_stats()


def update_spec(attr, old, new):
    is_ratio = new == "Ratio"
    spec_fig.yaxis.axis_label = "Specular Ratio (%)" if is_ratio else "Specular Reflectance"
    for r in black_spec_ratio_renderers:
        r.visible = is_ratio
    for r in black_spec_ref_renderers:
        r.visible = not is_ratio


def update_tot_slider(attr, old, new):
    total_fig.x_range.start, total_fig.x_range.end = new


def update_spec_slider(attr, old, new):
    spec_fig.x_range.start, spec_fig.x_range.end = new


def update_lamb_slider(attr, old, new):
    lamb_fig.x_range.start, lamb_fig.x_range.end = new


def update_multi_choice(attr, old, new):
    selected = set(multi_choice.value)
    for r in all_renderers:
        r.visible = r.name in selected
    tot_fig_label.visible = check_for_data(black_tot_renderers + white_tot_renderers)
    spec_fig_label.visible = check_for_data(black_spec_ref_renderers)
    lamb_fig_label.visible = check_for_data(white_lamb_renderers)
    _update_stats()


mat_color_select.on_change("value", update_mat_color)
spec_select.on_change("value", update_spec)
multi_choice.on_change("value", update_multi_choice)
tot_slider.on_change("value", update_tot_slider)
spec_slider.on_change("value", update_spec_slider)
lamb_slider.on_change("value", update_lamb_slider)

# ---------------------------------------------------------------------------
# JS download callbacks
# ---------------------------------------------------------------------------
download_js = open(join(dirname(__file__), "download.js")).read()
selec_js = open(join(dirname(__file__), "selec_download.js")).read()

totb_button.js_on_click(CustomJS(args=dict(source=black_tot_ds), code=download_js))
totw_button.js_on_click(CustomJS(args=dict(source=white_tot_ds), code=download_js))
spec_button.js_on_click(CustomJS(args=dict(source=black_spec_ref_ds), code=download_js))
spec_rat_button.js_on_click(CustomJS(args=dict(source=black_spec_ratio_ds), code=download_js))
lamb_button.js_on_click(CustomJS(args=dict(source=white_lamb_scaled_ds), code=download_js))
resid_button.js_on_click(CustomJS(args=dict(source=white_lamb_res_ds), code=download_js))
selec_button.js_on_click(
    CustomJS(args=dict(groups=checkbox_groups, rnds=all_renderers), code=selec_js)
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
""", name="band_legend", sizing_mode="stretch_width")

filter_layout = row(mat_color_select, spec_select, multi_choice, sizing_mode="stretch_width")
quick_zoom_row = row(uv_btn, vis_btn, nir_btn, full_btn, sizing_mode="stretch_width")
slider_layout = column(tot_slider, quick_zoom_row, spec_slider, lamb_slider, sizing_mode="stretch_width")
download_select_layout = row(
    column(btk_text, checkbox_groups[0]),
    column(wtk_text, checkbox_groups[1]),
    column(bsk_text, checkbox_groups[2], bsrk_text, checkbox_groups[3]),
    column(wls_text, checkbox_groups[4], wlss_text, checkbox_groups[5]),
    column(wrs_text, checkbox_groups[6]),
    sizing_mode="stretch_width",
)
download_buttons_layout = column(
    row(column(totb_button, totw_button), column(spec_button, spec_rat_button),
        column(lamb_button, resid_button)),
    selec_button,
)

tabs = Tabs(tabs=[
    TabPanel(child=instructions, title="Overview"),
    TabPanel(child=filter_layout, title="Filters"),
    TabPanel(child=slider_layout, title="Range Sliders"),
    TabPanel(child=download_select_layout, title="Select Data"),
    TabPanel(child=download_buttons_layout, title="Downloads"),
], active=0, name="tabs")

# ---------------------------------------------------------------------------
# Document
# ---------------------------------------------------------------------------
table_label = Div(
    text='<div style="font-weight:600; color:#00d2ff; font-size:13px; margin-bottom:4px;">Material Statistics</div>',
    sizing_mode="stretch_width",
)

curdoc().add_root(tabs)
curdoc().add_root(stats_div)
curdoc().add_root(column(table_label, summary_table, sizing_mode="stretch_width", name="summary_table"))
curdoc().add_root(band_legend)
curdoc().add_root(total_fig)
curdoc().add_root(spec_fig)
curdoc().add_root(lamb_fig)
curdoc().add_root(lamb_resid_fig)
curdoc().title = "B/W Materials Reflectance Data"
