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
    return Path, alt, date, datetime, mo, pl


@app.cell
def _(Path):
    _data_dir = (
        Path("src/markets_data_hub/data")
        if Path("src/markets_data_hub/data").exists()
        else Path("markets_data_hub/data")
    )
    rb_cert = str(_data_dir / "rb_cert_auctions_result.parquet")
    rb_gov = str(_data_dir / "sales_of_government_bonds.parquet")
    ref_rgk = str(_data_dir / "ref_rgk.xlsx")
    swestr = str(_data_dir / "swestr_values.parquet")
    policy_rate = str(_data_dir / "policy_rate_values.parquet")
    return policy_rate, rb_cert, rb_gov, ref_rgk, swestr


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
                            Marknadsdata
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
    # Marknadsoperationer
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Resultat från senaste auktion av Riksbankscertifikat
    """)
    return


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


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Försäljning av Statsobligationer
    """)
    return


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
        ])
        .with_columns([
            (
                (pl.col("_y2") - pl.col("_y1")) * 360
                + (pl.col("_m2") - pl.col("_m1")) * 30
                + pl.min_horizontal(pl.col("_d2"), pl.lit(30))
                - pl.min_horizontal(pl.col("_d1"), pl.lit(30))
            ).alias("_dagar_30e360")
        ])
        .with_columns([
            (pl.col("_dagar_30e360") / 360).alias("Aterstaende_lopetid_ar")
        ]).drop(["_y1", "_m1", "_d1", "_y2", "_m2", "_d2", "_dagar_30e360"])
        .with_columns([
            (pl.col("Budvolym") / pl.col("Tilldelad_volym")).alias("Bid_to_cover"),
        ]).filter(
            pl.col("Tilldelad_volym") > 0
        )
    )
    return (df_gov,)


@app.cell
def _(alt, df_gov, mo, pl):
    sgb_df = df_gov.filter(pl.col("Instrument/Marknad") == "SGB")
    sgb_il_df = df_gov.filter(pl.col("Instrument/Marknad") == "SGB IL")

    sgb_domain = sorted(sgb_df["Lan"].unique().to_list())
    sgb_il_domain = sorted(sgb_il_df["Lan"].unique().to_list())
    color_range = ["#0071B9", "#B91E2B", "#f4a700", "#2ca02c", "#9467bd", "#8c564b"]

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
                "Lan:N",
                scale=alt.Scale(domain=sgb_domain, range=color_range[: len(sgb_domain)]),
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=[
                alt.Tooltip("Anbudsdag:T", title="Datum"),
                alt.Tooltip("Lan:N", title="Obligation"),
                alt.Tooltip("Bid_to_cover:Q", title="Bid-to-cover", format=".2f"),
                alt.Tooltip("Budvolym:Q", title="Budvolym (Mkr)"),
                alt.Tooltip("Tilldelad_volym:Q", title="Tilldelad (Mkr)"),
                alt.Tooltip("Aterstaende_lopetid_ar:Q", title="Löptid (år)", format=".2f"),
            ],
        )
        .properties(
            title=alt.Title(text="Försäljning av Statsobligationer – Bid-to-cover per auktion", fontSize=16),
            width="container",
            height=400,
        )
        .configure_legend(columns=3, symbolType="square", symbolSize=100)
    )

    source_note = mo.Html("""
        <div style="font-size:11px; color:gray; text-align:left; padding: 4px 0 0 60px;">
            Anmärkning: Misslyckade auktioner (tilldelad volym = 0) är exkluderade.<br>
            Källa: Riksbanken/Riksgälden.
        </div>
    """)

    mo.vstack([
        btc_sgb_chart,
        source_note,
    ])
    return color_range, sgb_il_df, sgb_il_domain, source_note


@app.cell
def _(alt, color_range, mo, sgb_il_df, sgb_il_domain, source_note):
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
                "Lan:N",
                scale=alt.Scale(domain=sgb_il_domain, range=color_range[: len(sgb_il_domain)]),
                legend=alt.Legend(orient="bottom", title=None),
            ),
            tooltip=[
                alt.Tooltip("Anbudsdag:T", title="Datum"),
                alt.Tooltip("Lan:N", title="Obligation"),
                alt.Tooltip("Bid_to_cover:Q", title="Bid-to-cover", format=".2f"),
                alt.Tooltip("Budvolym:Q", title="Budvolym (Mkr)"),
                alt.Tooltip("Tilldelad_volym:Q", title="Tilldelad (Mkr)"),
                alt.Tooltip("Aterstaende_lopetid_ar:Q", title="Löptid (år)", format=".2f"),
            ],
        )
        .properties(
            title=alt.Title(text="Försäljning av Reala Statsobligationer – Bid-to-cover per auktion", fontSize=16),
            width="container",
            height=400,
        )
        .configure_legend(columns=3, symbolType="square", symbolSize=100)
    )


    mo.vstack([
        btc_sgb_il_chart,
        source_note,
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    # Kort penningmarknad
    """)
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Swestr senaste notering
    """)
    return


@app.cell
def _(pl, policy_rate, swestr):
    date_col = "date"

    df_swestr = pl.read_parquet(swestr)
    df_policy_rate = pl.read_parquet(policy_rate)

    cut = (
        df_swestr.filter(pl.col(date_col).dt.month() == 12)
          .group_by(pl.col(date_col).dt.year())
          .agg(pl.col(date_col).max().alias("last_dec"))
          .select("last_dec")
    )

    df_swestr = (
        df_swestr
        .filter(~pl.col(date_col).is_in(cut["last_dec"].implode()))
        .join(df_policy_rate, on="date")
        .rename({
            "value" : "policy_rate"
        })
        .with_columns(
            (pl.col.rate - pl.col.policy_rate).alias("diff_swestr")
        )
    )
    return (df_swestr,)


@app.cell
def _(df_swestr, mo):
    swestr_row = df_swestr.sort("date").tail(1).row(0, named=True)

    def swestr_card(stat):
        return mo.Html(f'<div style="flex:1">{stat.text}</div>')

    mo.hstack([
        swestr_card(mo.stat(value=f"{swestr_row['rate']:.3f} %", label="SWESTR", bordered=True)),
        swestr_card(mo.stat(value=f"{swestr_row['volume']:,.0f} MSEK", label="Volym", bordered=True)),
        swestr_card(mo.stat(value=str(swestr_row['numberOfTransactions']), label="Antal transaktioner", bordered=True)),
        swestr_card(mo.stat(value=str(swestr_row['numberOfAgents']), label="Antal rapportörer", bordered=True)),
    ])
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Swestrs utveckling senaste månaden
    """)
    return


@app.cell
def _(alt, df_swestr, mo, pl):
    def swestr_boxplot():
        latest_month = df_swestr.sort("date").tail(1)["date"][0]

        df_box = (
            df_swestr
            .filter(
                (pl.col("date").dt.year() == latest_month.year) &
                (pl.col("date").dt.month() == latest_month.month)
            )
            .select(["date", "rate", "pctl12_5", "pctl87_5"])
            .unpivot(
                index="date",
                on=["rate", "pctl12_5", "pctl87_5"],
                variable_name="serie",
                value_name="värde",
            )
            .with_columns(pl.col("date").cast(pl.Utf8))
        )

        chart = (
            alt.Chart(df_box)
            .mark_boxplot(extent="min-max")
            .encode(
                x=alt.X("date:O", axis=alt.Axis(title="", labelAngle=-45)),
                y=alt.Y(
                    "värde:Q",
                    axis=alt.Axis(title="Ränta (%)"),
                    scale=alt.Scale(zero=False),
                ),
            )
            .properties(
                title=alt.Title(
                    text=f"Swestr notering under den senaste månaden",
                    fontSize=16,
                ),
                width="container",
                height=400,
            )
        )

        return mo.vstack([
            chart,
            mo.Html("""
                <div style="font-size:11px; color:gray; text-align:left; padding: 4px 0 0 0px;">
                    Lådan visar spridningen mellan nedre/övre trimningsgräns och Swestrnoteringen per dag.<br>
                    Källa: Riksbanken.
                </div>
            """),
        ])

    swestr_boxplot()
    return


@app.cell(hide_code=True)
def _(mo):
    mo.md(r"""
    ## Swestr över tid
    """)
    return


@app.cell
def _(alt, df_swestr, mo, pl):
    def swestr_band():
        # Smält om till långt format för legend
        df_long = df_swestr.select(["date", "rate", "policy_rate"]).unpivot(
            index="date",
            on=["rate", "policy_rate"],
            variable_name="serie",
            value_name="värde",
        ).with_columns(
            pl.col("serie").replace({"rate": "SWESTR", "policy_rate": "Styrränta"})
        )

        _domain = ["SWESTR", "Styrränta"]
        _colors = ["#0071B9", "#B91E2B"]
        _dash = [[1, 0], [4, 2]]

        lines = (
            alt.Chart(df_long)
            .mark_line(strokeWidth=1.5)
            .encode(
                x=alt.X("date:T", axis=alt.Axis(title="", format="%Y", tickCount="year")),
                y=alt.Y("värde:Q", scale=alt.Scale(zero=False), axis=alt.Axis(title="Ränta (%)")),
                color=alt.Color(
                    "serie:N",
                    scale=alt.Scale(domain=_domain, range=_colors),
                    legend=alt.Legend(orient="bottom", title=None),
                ),
                strokeDash=alt.StrokeDash(
                    "serie:N",
                    scale=alt.Scale(domain=_domain, range=_dash),
                    legend=None,
                ),
                tooltip=[
                    alt.Tooltip("date:T", title="Datum"),
                    alt.Tooltip("serie:N", title="Serie"),
                    alt.Tooltip("värde:Q", title="Ränta (%)", format=".3f"),
                ],
            )
        )

        spread = (
            alt.Chart(df_swestr)
            .mark_area(opacity=0.15, color="#f4a700")
            .encode(
                x=alt.X("date:T"),
                y=alt.Y("rate:Q"),
                y2=alt.Y2("policy_rate:Q"),
            )
        )

        chart_rates = (
            alt.layer(spread, lines)
            .properties(
                title=alt.Title(text="Styrränta vs Swestr", fontSize=16),
                width="container",
                height=300,
            )
            .configure_legend(columns=2, symbolType="stroke", symbolSize=100)
        )

        diff_line = (
            alt.Chart(df_swestr)
            .mark_line(color="#f4a700", strokeWidth=1.5)
            .encode(
                x=alt.X("date:T", axis=alt.Axis(title="", format="%Y", tickCount="year")),
                y=alt.Y("diff_swestr:Q", axis=alt.Axis(title="Diff (%)")),
                tooltip=[
                    alt.Tooltip("date:T", title="Datum"),
                    alt.Tooltip("diff_swestr:Q", title="Diff Styrränta - Swestr", format=".4f"),
                ],
            )
        )

        diff_zero = (
            alt.Chart(df_swestr)
            .mark_rule(color="#475569", strokeDash=[2, 2])
            .encode(y=alt.datum(0))
        )

        chart_diff = (
            alt.layer(diff_zero, diff_line)
            .properties(
                title=alt.Title(text="Avvikelse från styrräntan", fontSize=16),
                width="container",
                height=200,
            )
        )

        return mo.vstack([
            chart_rates,
            chart_diff,
            mo.Html("""
                <div style="font-size:11px; color:gray; text-align:left; padding: 4px 0 0 0px;">
                    Gula fältet visar spreaden mellan styrränta och Swestr. Swestr noteringen för sista december är exkluderad.<br>
                    Källa: Riksbanken.
                </div>
            """),
        ])

    swestr_band()
    return


if __name__ == "__main__":
    app.run()
