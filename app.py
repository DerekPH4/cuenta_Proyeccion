from flask import Flask, request, render_template, redirect, url_for
import pandas as pd
import os

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = 'uploads'
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

df = None
cajas_corregidas = {}

@app.route("/", methods=["GET"])
def index():
    return render_template("index.html")

@app.route("/upload", methods=["POST"])
def upload():
    global df, cajas_corregidas
    archivo = request.files["archivo"]
    if archivo:
        path = os.path.join(app.config['UPLOAD_FOLDER'], archivo.filename)
        archivo.save(path)

        # Leer archivo crudo
        df_raw = pd.read_excel(path, sheet_name="SOMBREROS", header=None)

        # Detectar cajas
        cajas_corregidas = {}
        caja_actual = None
        for i in range(len(df_raw)):
            valor = str(df_raw.iat[i, 1]).strip().upper() if pd.notna(df_raw.iat[i, 1]) else ""
            if valor == "CAJA" and pd.notna(df_raw.iat[i + 1, 1]):
                posible_caja = str(df_raw.iat[i + 1, 1]).strip().upper().replace('\n', ' ')
                if posible_caja:
                    caja_actual = posible_caja
            cajas_corregidas[i] = caja_actual

        # Procesar archivo limpio
        df_clean = pd.read_excel(path, sheet_name="SOMBREROS", header=None)
        df_clean.columns = df_clean.iloc[2]
        df_clean = df_clean[3:].copy()
        df_clean.rename(columns=lambda x: x.strip() if isinstance(x, str) else x, inplace=True)
        df_clean["Cliente"] = df_clean["Cliente"].astype(str).str.strip().str.upper()
        df_clean["ID"] = df_clean["ID"].astype(str).str.strip().str.upper()
        df_clean["Caja"] = df_clean.index.map(cajas_corregidas).fillna("DESCONOCIDA")

        df = df_clean

    return redirect(url_for("index"))

@app.route("/buscar")
def buscar():
    global df
    cliente_query = request.args.get("cliente", "").strip().upper()
    if df is None:
        return "<h2 style='color:white'>Primero carga un archivo</h2>"

    filtrado = df[df["Cliente"].str.contains(cliente_query, na=False) | df["ID"].str.contains(cliente_query, na=False)]
    
    # Página personalizada si no se encuentra el cliente
    if filtrado.empty:
        return """
        <html>
        <head>
            <title>Cliente no encontrado</title>
            <style>
                body {
                    background-color: black;
                    color: white;
                    font-family: Arial, sans-serif;
                    text-align: center;
                    padding: 80px;
                }

                .mensaje {
                    font-size: 24px;
                    color: #bf0228;
                    margin-bottom: 30px;
                }

                .volver {
                    display: inline-block;
                    margin-top: 20px;
                    color: #bf0228;
                    text-decoration: none;
                    font-weight: bold;
                    border: 2px solid #bf0228;
                    padding: 10px 20px;
                    border-radius: 8px;
                    transition: background 0.3s;
                }

                .volver:hover {
                    background-color: #bf0228;
                    color: black;
                }
            </style>
        </head>
        <body>
            <div class="mensaje">❌ Cliente no encontrado.<br>Por favor verifica que el nombre o ID esté escrito correctamente.</div>
            <a class="volver" href="/">Volver</a>
        </body>
        </html>
        """

    primer_cliente = filtrado.iloc[0]["Cliente"]
    primer_id = filtrado.iloc[0]["ID"]
    nombre_base = primer_cliente

    grouped = filtrado.groupby(["Caja", "TX"]).size().reset_index(name="Cantidad")
    total = grouped["Cantidad"].sum()
    tabla_html = grouped.to_html(index=False, classes="tabla-resultados")

    html = f"""
    <html>
    <head>
        <title>Resultados</title>
        <style>
            body {{
                background-color: black;
                color: white;
                font-family: Arial, sans-serif;
                padding: 40px;
                text-align: center;
            }}

            .header {{
                display: flex;
                justify-content: center;
                align-items: center;
                gap: 15px;
                margin-bottom: 40px;
            }}

            .header h1 {{
                color: #bf0228;
                font-size: 48px;
                margin: 0;
                text-shadow:
                  -1px -1px 0 white,
                   1px -1px 0 white,
                  -1px  1px 0 white,
                   1px  1px 0 white;
            }}

            .logo {{
                height: 80px;
            }}

            h2 {{
                margin: 10px 0;
                font-size: 22px;
            }}

            .tabla-resultados {{
                margin: 30px auto;
                border-collapse: collapse;
                width: 60%;
            }}

            .tabla-resultados th,
            .tabla-resultados td {{
                border: 1px solid white;
                padding: 10px;
                text-align: center;
            }}

            .tabla-resultados tr:hover {{
                background-color: #222;
            }}

            .total-box {{
                margin-top: 15px;
                display: flex;
                justify-content: center;
                gap: 5px;
            }}

            .total-box td {{
                border: 1px solid white;
                padding: 8px 20px;
                font-weight: bold;
                background-color: black;
                color: #bf0228;
            }}

            .volver {{
                display: inline-block;
                margin-top: 30px;
                color: #bf0228;
                text-decoration: none;
                font-weight: bold;
                border: 2px solid #bf0228;
                padding: 10px 20px;
                border-radius: 8px;
                transition: background 0.3s;
            }}

            .volver:hover {{
                background-color: #bf0228;
                color: black;
            }}
        </style>
    </head>
    <body>
        <div class="header">
            <h1>PRO</h1>
            <img src="/static/logo.png" class="logo">
            <h1>HATS</h1>
        </div>

        <h2>🧾 Cliente: <span style="color:#bf0228;">{nombre_base}</span></h2>
        <h2>🔠 ID: <span style="color:#bf0228;">{primer_id}</span></h2>
        {tabla_html}
        <table class="total-box">
            <tr>
                <td>Total</td>
                <td>{total}</td>
            </tr>
        </table>
        <a class="volver" href="/">Volver</a>
    </body>
    </html>
    """
    return html

if __name__ == "__main__":
    app.run(debug=True)
