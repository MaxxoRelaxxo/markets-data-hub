import marimo

__generated_with = "0.20.1"
app = marimo.App(
    width="full",
    app_title="Marknadsoperationer",
    auto_download=["html"],
)


@app.cell
def _():
    import marimo as mo
    import polars as pl
    import altair as alt
    from pathlib import Path
    from datetime import date, datetime

    def setup_altair():
        alt.renderers.set_embed_options(actions=False)

    setup_altair()
    return alt, date, datetime, mo, pl


@app.cell
def _():
    rb_cert = "src/markets_data_hub/data/rb_cert_auctions_result.parquet"
    rb_gov = "src/markets_data_hub/data/sales_of_government_bonds.parquet"
    ref_rgk = "src/markets_data_hub/data/ref_rgk.xlsx"
    return rb_cert, rb_gov, ref_rgk


@app.cell
def _(pl, rb_cert):
    df_cert = (
        pl.read_parquet(rb_cert)
        .sort("Anbudsdag")
        .with_columns(
            (pl.col.Erbjuden_volym - pl.col.Tilldelad_volym).round(1).alias("Återstående_likviditetsöverskott"),
            (pl.col("Erbjuden_volym") - pl.col("Erbjuden_volym").shift(1)).round(1).alias("Delta_Erbjuden_volym"),
            (pl.col("Tilldelad_volym") - pl.col("Tilldelad_volym").shift(1)).round(1).alias("Delta_Tilldelad_volym"),
            (pl.col("Antal_bud") - pl.col("Antal_bud").shift(1)).round(1).alias("Delta_Antal_bud"),
        )
        .with_columns(
            (pl.col("Återstående_likviditetsöverskott") - pl.col("Återstående_likviditetsöverskott").shift(1)).alias("Delta_Återstående_likviditetsöverskott")
        )
    )
    return (df_cert,)


@app.cell
def _(pl, rb_gov, ref_rgk):
    cols = [
      "Instrument/Marknad",
      "Värdepapper",
      "ISIN",
      "ISIN US",
      "Utgivnings-dag",
      "Valuta",
      "Kupong-ränta",
      "Kupong-frekvens",
      "Kupong från",
      "BasKPI",
      "Dagkon-vention",
      "Kupong-typ"
    ]

    ref_rgk_df = pl.read_excel(ref_rgk, columns=cols)

    df_gov = (
        pl.read_parquet(rb_gov)
        .join(ref_rgk_df, left_on="Isin", right_on="ISIN")
        .sort("Anbudsdag", "Isin")
        .with_columns([
            # Extrahera datumkomponenter
            pl.col("Anbudsdag").dt.year().alias("_y1"),
            pl.col("Anbudsdag").dt.month().alias("_m1"),
            pl.col("Anbudsdag").dt.day().alias("_d1"),
            pl.col("Forfallodag").cast(pl.Date).dt.year().alias("_y2"),
            pl.col("Forfallodag").cast(pl.Date).dt.month().alias("_m2"),
            pl.col("Forfallodag").cast(pl.Date).dt.day().alias("_d2"),
        ]).with_columns([
            (
                (pl.col("_y2") - pl.col("_y1")) * 360
                + (pl.col("_m2") - pl.col("_m1")) * 30
                + pl.min_horizontal(pl.col("_d2"), pl.lit(30))
                - pl.min_horizontal(pl.col("_d1"), pl.lit(30))
            ).alias("_dagar_30e360")
        ]).with_columns([
            (pl.col("_dagar_30e360") / 360).alias("Aterstaende_lopetid_ar")
        ]).drop(["_y1", "_m1", "_d1", "_y2", "_m2", "_d2", "_dagar_30e360"])
    )
    df_gov
    return (df_gov,)


@app.cell
def _(datetime, mo):
    month = {
        1: "Januari", 2: "Februari", 3: "Mars", 4: "April",
        5: "Maj", 6: "Juni", 7: "Juli", 8: "Augusti",
        9: "September", 10: "Oktober", 11: "November", 12: "December"
    }
    now = datetime.now()
    week = now.isocalendar().week
    datum_text = f"Vecka {week} - {now.year}"        
    publicerat_text = now.strftime("%Y-%m-%d")

    header = mo.Html(
        f"""
        <style>
            .page {{
                width: 100%;
                font-family: 'Calibri', sans-serif;
            }}
            .two-col {{
                display: grid;
                grid-template-columns: 1fr 220px;
                column-gap: 24px;
                align-items: center;
            }}
            .logo {{
                justify-self: end;
                height: 200px;
                max-width: 100%;
                object-fit: contain;
            }}
            .meta-bg {{
                background: #F2F2F2;
                box-shadow: 0 1px 3px rgba(0,0,0,0.1);
                margin-top: 30px;
            }}
            .meta-inner {{
                padding: 16px 0;
            }}
            .meta-cols {{
                display: grid;
                grid-template-columns: 1fr 220px;
                column-gap: 24px;
                align-items: start;
            }}
            .meta-right {{
                text-align: right;
            }}
        </style>
        <div class="page">
            <div style="background: white;">
                <div class="two-col" style="padding-top: 16px; padding-bottom: 16px;">
                    <div>
                        <h1 style="margin:0; font-size:4.1rem; font-weight:700; line-height:1.1;">
                            Marknadsoperationer Riksbankscertifikat
                        </h1>
                        <div style="margin-top:6px; font-size:1rem; color:#666;">
                            {datum_text}
                        </div>
                    </div>
                </div>
            </div>
            <div style="height: 30px;"></div>
        </div>
        """
    )
    header
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Resultat från senaste auktion av Riksbankscertifikat
    """)
    return


@app.cell
def _(df_cert, mo):
    row = df_cert.row(-1, named=True)

    def card(stat):
        return mo.Html(f'<div style="flex:1">{stat.text}</div>')

    mo.hstack([
        card(mo.stat(value=f"{row[col]:.1f} mdkr", label=label, caption=f"{row[delta]:+.1f} mdkr", bordered=True))
        for col, label, delta in [
            ("Erbjuden_volym", "Erbjuden volym", "Delta_Erbjuden_volym"),
            ("Tilldelad_volym", "Tilldelad volym", "Delta_Tilldelad_volym"),
            ("Återstående_likviditetsöverskott", "Återstående likviditetsöverskott", "Delta_Återstående_likviditetsöverskott"),
        ]
    ] + [
        card(mo.stat(value=str(row['Antal_bud']), label="Antal bud", caption=f"Δ {row['Delta_Antal_bud']:+.0f}", bordered=True)),
    ])
    return


@app.cell
def _(alt, date, df_cert, mo, pl):
    order_map = {
        "Erbjuden_volym": (1, "Erbjuden volym"),
        "Återstående_likviditetsöverskott": (2, "Återstående likviditetsöverskott"),
        "Räntefri inlåning": (3, "Räntefri inlåning"),
    }

    deposit_req = pl.DataFrame({
        "Anbudsdag": [date(2025,10,14), date(2025,11,21), date(2025,10,28), date(2025,11,4)],
        "variable": "Räntefri inlåning",
        "value": [40.055, 40.055, 40.055, 40.055]
    })

    rb_cert_plot_df = (
        df_cert
        .unpivot(
            index="Anbudsdag",
            on=["Erbjuden_volym", "Återstående_likviditetsöverskott"]
        )
    )

    rb_cert_plot_df = pl.concat([rb_cert_plot_df, deposit_req])

    # Komplett datumgrid
    all_dates = rb_cert_plot_df.select("Anbudsdag").unique()
    all_variables = pl.DataFrame({"variable": ["Erbjuden_volym", "Återstående_likviditetsöverskott", "Räntefri inlåning"]})
    full_grid = all_dates.join(all_variables, how="cross")

    rb_cert_plot_df = (
        rb_cert_plot_df
        .join(full_grid, on=["Anbudsdag", "variable"], how="right")
        .sort(["variable", "Anbudsdag"])
        .with_columns(
            pl.col("value").forward_fill().over("variable")
        )
        .fill_null(0)
        .with_columns(
            pl.col("variable").replace(
                {k: v[1] for k, v in order_map.items()}
            ).alias("variable")
        )
    )

    domain = ["Erbjuden volym", "Återstående likviditetsöverskott", "Räntefri inlåning"]

    cert_plot = (
        alt.Chart(rb_cert_plot_df)
        .mark_area(opacity=0.7)
        .encode(
            x=alt.X(
                "Anbudsdag:T",
                axis=alt.Axis(title="", format="%Y", tickCount="year")
            ),
            y=alt.Y(
                "value:Q",
                axis=alt.Axis(title="Miljarder kr"),
                stack="zero",
            ),
            color=alt.Color(
                "variable:N",
                scale=alt.Scale(
                    domain=domain,
                    range=["#0071B9", "#B91E2B", "#f4a700"]
                ),
                legend=alt.Legend(orient="bottom", title=None)
            ),
            order=alt.Order("variable:N", sort="ascending"),
        )
        .properties(
            title=alt.Title(
                text="Likviditetsöverskott över tid",
                fontSize=16,
            ),
            width="container",
            height=400,
        )
        .configure_legend(
            columns=3,
            symbolType="square",
            symbolSize=100,
        )
    )

    mo.vstack([
        cert_plot,
        mo.Html("""
            <div style="font-size:11px; color:gray; text-align:left; padding: 4px 0 0 60px;">
                Anmärkning: Grafen omfattar ej återförsäljning av riksbankscertifikat eller finjusterade transaktioner. Likviditetsställningen mot banksystemet kan därför avvika från vad som framgår av grafen.<br>
                Källa: Riksbanken.
            </div>
        """)
    ])
    return


@app.cell
def _(alt, df_gov, mo, pl):
    # ── Auktionsyield över tid – SGB ─────────────────────────────────────────────
    sgb_df = df_gov.filter(pl.col("Instrument/Marknad") == "SGB")
    sgb_domain = sorted(sgb_df["Värdepapper"].unique().to_list())
    sgb_range = ["#0071B9", "#B91E2B", "#f4a700", "#2ca02c", "#9467bd", "#8c564b"]

    yield_chart_sgb = (
        alt.Chart(sgb_df)
        .mark_line(point=True, opacity=0.8)
        .encode(
            x=alt.X(
                "Anbudsdag:T",
                axis=alt.Axis(title="", format="%Y", tickCount="year"),
            ),
            y=alt.Y(
                "Genomsnittlig_ranta:Q",
                axis=alt.Axis(title="Auktionsyield (%)"),
                scale=alt.Scale(zero=False),
            ),
            color=alt.Color(
                "Värdepapper:N",
                scale=alt.Scale(domain=sgb_domain, range=sgb_range[: len(sgb_domain)]),
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=[
                alt.Tooltip("Anbudsdag:T", title="Datum"),
                alt.Tooltip("Värdepapper:N", title="Obligation"),
                alt.Tooltip("Genomsnittlig_ranta:Q", title="Yield (%)", format=".3f"),
                alt.Tooltip("Aterstaende_lopetid_ar:Q", title="Löptid (år)", format=".2f"),
            ],
        )
        .properties(
            title=alt.Title(text="SGB – Auktionsyield (YTM) över tid", fontSize=16),
            width="container",
            height=400,
        )
        .configure_legend(columns=3, symbolType="stroke", symbolSize=100)
        .interactive()
    )

    # ── Auktionsyield över tid – SGB IL ──────────────────────────────────────────
    sgb_il_df = df_gov.filter(pl.col("Instrument/Marknad") == "SGB IL")
    sgb_il_domain = sorted(sgb_il_df["Värdepapper"].unique().to_list())

    yield_chart_sgb_il = (
        alt.Chart(sgb_il_df)
        .mark_line(point=True, opacity=0.8)
        .encode(
            x=alt.X(
                "Anbudsdag:T",
                axis=alt.Axis(title="", format="%Y", tickCount="year"),
            ),
            y=alt.Y(
                "Genomsnittlig_ranta:Q",
                axis=alt.Axis(title="Realränta (%)"),
                scale=alt.Scale(zero=False),
            ),
            color=alt.Color(
                "Värdepapper:N",
                scale=alt.Scale(domain=sgb_il_domain, range=sgb_range[: len(sgb_il_domain)]),
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=[
                alt.Tooltip("Anbudsdag:T", title="Datum"),
                alt.Tooltip("Värdepapper:N", title="Obligation"),
                alt.Tooltip("Genomsnittlig_ranta:Q", title="Realränta (%)", format=".3f"),
                alt.Tooltip("Aterstaende_lopetid_ar:Q", title="Löptid (år)", format=".2f"),
            ],
        )
        .properties(
            title=alt.Title(text="SGB IL – Auktionsyield (realränta) över tid", fontSize=16),
            width="container",
            height=400,
        )
        .configure_legend(columns=3, symbolType="stroke", symbolSize=100)
        .interactive()
    )

    # ── Bid-to-cover – SGB ───────────────────────────────────────────────────────
    btc_sgb_chart = (
        alt.Chart(sgb_df)
        .mark_bar(opacity=0.7)
        .encode(
            x=alt.X(
                "Anbudsdag:T",
                axis=alt.Axis(title="", format="%Y", tickCount="year"),
            ),
            y=alt.Y(
                "Bid_to_cover:Q",
                axis=alt.Axis(title="Bid-to-cover"),
            ),
            color=alt.Color(
                "Värdepapper:N",
                scale=alt.Scale(domain=sgb_domain, range=sgb_range[: len(sgb_domain)]),
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=[
                alt.Tooltip("Anbudsdag:T", title="Datum"),
                alt.Tooltip("Värdepapper:N", title="Obligation"),
                alt.Tooltip("Bid_to_cover:Q", title="Bid-to-cover", format=".2f"),
                alt.Tooltip("Budvolym:Q", title="Budvolym (Mkr)"),
                alt.Tooltip("Tilldelad_volym:Q", title="Tilldelad (Mkr)"),
            ],
        )
        .properties(
            title=alt.Title(text="SGB – Bid-to-cover per auktion", fontSize=16),
            width="container",
            height=400,
        )
        .configure_legend(columns=3, symbolType="square", symbolSize=100)
        .interactive()
    )

    # ── Bid-to-cover – SGB IL ────────────────────────────────────────────────────
    btc_sgb_il_chart = (
        alt.Chart(sgb_il_df)
        .mark_bar(opacity=0.7)
        .encode(
            x=alt.X(
                "Anbudsdag:T",
                axis=alt.Axis(title="", format="%Y", tickCount="year"),
            ),
            y=alt.Y(
                "Bid_to_cover:Q",
                axis=alt.Axis(title="Bid-to-cover"),
            ),
            color=alt.Color(
                "Värdepapper:N",
                scale=alt.Scale(domain=sgb_il_domain, range=sgb_range[: len(sgb_il_domain)]),
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=[
                alt.Tooltip("Anbudsdag:T", title="Datum"),
                alt.Tooltip("Värdepapper:N", title="Obligation"),
                alt.Tooltip("Bid_to_cover:Q", title="Bid-to-cover", format=".2f"),
                alt.Tooltip("Budvolym:Q", title="Budvolym (Mkr)"),
                alt.Tooltip("Tilldelad_volym:Q", title="Tilldelad (Mkr)"),
            ],
        )
        .properties(
            title=alt.Title(text="SGB IL – Bid-to-cover per auktion", fontSize=16),
            width="container",
            height=400,
        )
        .configure_legend(columns=3, symbolType="square", symbolSize=100)
        .interactive()
    )

    # ── Rendera ───────────────────────────────────────────────────────────────────
    source_note = mo.Html("""
        <div style="font-size:11px; color:gray; text-align:left; padding: 4px 0 0 60px;">
            Anmärkning: Misslyckade auktioner (tilldelad volym = 0) är exkluderade.
            Yield avser genomsnittlig yield-to-maturity vid auktionsdagen, ej kupongränta.<br>
            Källa: Riksbanken/Riksgälden.
        </div>
    """)

    mo.vstack([
        yield_chart_sgb,
        source_note,
        yield_chart_sgb_il,
        source_note,
        btc_sgb_chart,
        source_note,
        btc_sgb_il_chart,
        source_note,
    ])
    return


if __name__ == "__main__":
    app.run()
