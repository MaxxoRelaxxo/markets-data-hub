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

    return alt, date, datetime, mo, pl


@app.cell
def _():
    rb_cert = "src/markets_data_hub/data/rb_cert_auctions_result.parquet"
    rb_gov = "src/markets_data_hub/data/sales_of_government_bonds.parquet"
    return rb_cert, rb_gov


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
def _(pl, rb_gov):
    df_gov = (
        pl.read_parquet(rb_gov)
    )
    return


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
                Anmärkning: Grafen omfattar ej återförsäljning av riksbankscertifikat eller finjusterade transaktioner. Den återstående likviditeten kan därför avvika från vad som framgår av grafen.<br>
                Källa: Riksbanken.
            </div>
        """)
    ])
    return


if __name__ == "__main__":
    app.run()
