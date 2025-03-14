import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd
import pyproj
from PIL import Image
import streamlit as st


img = Image.open("CyL.png")
st.set_page_config(page_title="CyL en mapas", page_icon=img, layout="wide")

st.markdown(
    """
    <style>
    [data-testid="stSidebar"][aria-expanded="true"] > div:first-child{
        width: 175px;
    }
    [data-testid="stSidebar"][aria-expanded="false"] > div:first-child{
        width: 175px;
        margin-left: -400px;
    }

    """,
    unsafe_allow_html=True,
)

st.markdown("""
    <div style="background-color:#FF815F;padding:0px">
    <h1 style="color:#FFFFFF ;text-align:center;">Elecciones en Castilla y León 13F</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown("<h4 style='text-align: center; '>Los resultados de las elecciones del 13F en Castilla y León a través de mapas interactivos</h4>",
            unsafe_allow_html=True)

st.markdown("<h5 style='text-align: center; '>"
            "¿Cuál ha sido el resultado en tu municipio? ¡Descúbrelo en el mapa!</h5>",
            unsafe_allow_html=True)

modo = st.sidebar.radio(label="Elija el modo de visualización",
                        options=['% de voto por partidos', 'Ganador de las elecciones'],
                        help="Podrá visualizar, por un lado, mapas correspondientes al resultado de cada partido"
                             " en cada provincia. También tiene la opción de ver cada municipio coloreado"
                             " según el partido ganador, o el segundo más votado")

c1, c2, c3 = st.columns((1, 1, 1))
with c1:
    tipo_elecciones = st.selectbox('Elija el tipo de elecciones:',
                                  ('Autonómicas', 'Generales'))

if modo == 'Ganador de las elecciones':
    with c2:
        provincia_elegida = st.selectbox('Elija qué provincia desea visualizar:',
                                         ('Ávila', 'Burgos', 'León', 'Palencia', 'Salamanca',
                                          'Segovia', 'Soria', 'Valladolid', 'Zamora'), index=4)
    with c3:
        ganador = st.selectbox('Cada municipio tendrá el color del:',
                               ('Ganador', 'Segundo'))
else:
    with c2:
        provincia_elegida = st.selectbox('Elija qué provincia desea visualizar:',
                                         ('Ávila', 'Burgos', 'León', 'Palencia', 'Salamanca',
                                          'Segovia', 'Soria', 'Valladolid', 'Zamora', 'Castilla y León'), index=4)
    with c3:
        partido_elegido = st.selectbox('Elija un partido:',
                                       ('Participación', 'PP', 'PSOE', 'VOX', 'Podemos', 'Ciudadanos', 'UPL', 'XAV',
                                        'España Vaciada', 'Soria ¡YA!'))


@st.cache_data(show_spinner=False)
def seleccionar_elecciones(provincia, elecciones):
    """
    Selecciona el archivo de datos que contiene los datos de las elecciones elegidas por el usuario

    Parámetros
    ----------
    elecciones: str
    """
    if elecciones == "Autonómicas":
        cyl_datos = pd.read_excel("CyL elecciones autonómicas.xlsb")
    else:
        cyl_datos = pd.read_excel("CyL generales.xlsb")

    if (modo == '% de voto por partidos') & (elecciones == "Autonómicas"):
        if (partido_elegido == "VOX") | (partido_elegido == "Ciudadanos") | (partido_elegido == "Podemos"):
            cyl_datos = cyl_datos[cyl_datos["Elecciones"] >= 2015]
        elif (partido_elegido == "UPL") & ((provincia == "León") | (provincia == "Zamora")):
            cyl_datos = cyl_datos[cyl_datos["Elecciones"] >= 2011]
        elif (partido_elegido == "UPL") & (provincia == "Salamanca"):
            cyl_datos = cyl_datos[(cyl_datos["Elecciones"] == 2019) | (cyl_datos["Elecciones"] == 2022)]
        elif partido_elegido == "XAV":
            cyl_datos = cyl_datos[(cyl_datos["Elecciones"] == 2019) | (cyl_datos["Elecciones"] == 2022)]
        elif (partido_elegido == "España Vaciada") | (partido_elegido == "Soria ¡YA!"):
            cyl_datos = cyl_datos[cyl_datos["Elecciones"] == 2022]

    elif (modo == "% de voto por partidos") & (elecciones == "Generales"):
        if (partido_elegido == "VOX") | (partido_elegido == "Ciudadanos") | (partido_elegido == "Podemos"):
            cyl_datos = cyl_datos[cyl_datos["Elecciones"] != "Noviembre 2011"]
        elif partido_elegido == "UPL":
            cyl_datos = cyl_datos[(cyl_datos["Elecciones"] == "Junio 2016") | (cyl_datos["Elecciones"] == "Noviembre 2019")]
        elif partido_elegido == "XAV":
            cyl_datos = cyl_datos[cyl_datos["Elecciones"] == "Noviembre 2019"]
        elif (partido_elegido == "España Vaciada") | (partido_elegido == "Soria ¡YA!"):
            st.warning("El partido seleccionado no se ha presentado a las elecciones generales")

    else:
        pass

    cyl_datos["codmun"] = cyl_datos["codmun"].astype(int)

    return cyl_datos


@st.cache_data(show_spinner=False)
def seleccionar_provincia(mapa, provincia):
    """
    Selecciona la provincia de Castilla y León (o Castilla y León en su conjunto) que se desea visualizar.

    Parámetros
    ----------
    mapa: shape file
    provincia: str
    """

    zoom_provincia = 0
    center_provincia = {}
    if provincia == 'Castilla y León':
        zoom_provincia = 6.5
        center_provincia = {"lat": 41.6300, "lon": -4.2700}
        mapa_provincia = mapa
    else:
        codigo_provincia = ""
        for prov, codigo, zoom, center in (
                                           ("Ávila", "05", 8, {"lat": 40.6300, "lon": -5.0000}),
                                           ("Burgos", "09", 7.3, {"lat": 42.3316, "lon": -3.5000}),
                                           ("León", "24", 7.8, {"lat": 42.6346, "lon": -5.9724}),
                                           ("Palencia", "34", 7.75, {"lat": 42.4000, "lon": -4.5400}),
                                           ("Salamanca", "37", 8, {"lat": 40.7500, "lon": -6.0255}),
                                           ("Segovia", "40", 8.2, {"lat": 41.1000, "lon": -4.0000}),
                                           ("Soria", "42", 8, {"lat": 41.6000, "lon": -2.5959}),
                                           ("Valladolid", "47", 7.85, {"lat": 41.6987, "lon": -4.8418}),
                                           ("Zamora", "49", 8, {"lat": 41.6880, "lon": -6.0919})
        ):
            if prov == provincia:
                codigo_provincia = codigo
                zoom_provincia = zoom
                center_provincia = center

        mapa = mapa[mapa["c_prov_id"] == codigo_provincia]

    mapa.to_crs(pyproj.CRS.from_epsg(4326), inplace=True)
    mapa["codmun"] = mapa["codmun"].astype(int)

    return mapa, zoom_provincia, center_provincia


@st.cache_data(suppress_st_warning=True, show_spinner=False)
def pintar_mapa_ganador(mapa_provincia_merged, zoom_arg, coordenadas, elecciones):
    """
    Devuelve el mapa de Castilla y León o de una de sus provincias con cada municipio del color del partido ganador
    de las elecciones elegidas por el usuario

    Parámetros
    ----------
    mapa_provincia_merged: geopandas
    zoom_arg: int
    coordenadas: dict
    """
    if elecciones == "Autonómicas":
        copia = pd.concat([mapa_provincia_merged[(mapa_provincia_merged["Elecciones"] == 2011)].tail(9).copy(),
                           mapa_provincia_merged[(mapa_provincia_merged["Elecciones"] == 2015)].tail(9).copy(),
                           mapa_provincia_merged[(mapa_provincia_merged["Elecciones"] == 2019)].tail(9).copy(),
                           mapa_provincia_merged[(mapa_provincia_merged["Elecciones"] == 2022)].tail(9).copy()])

    else:
        copia = pd.concat([mapa_provincia_merged[(mapa_provincia_merged["Elecciones"] == "Noviembre 2011")].tail(9).copy(),
                           mapa_provincia_merged[(mapa_provincia_merged["Elecciones"] == "Diciembre 2015")].tail(9).copy(),
                           mapa_provincia_merged[(mapa_provincia_merged["Elecciones"] == "Junio 2016")].tail(9).copy(),
                           mapa_provincia_merged[(mapa_provincia_merged["Elecciones"] == "Abril 2019")].tail(9).copy(),
                           mapa_provincia_merged[(mapa_provincia_merged["Elecciones"] == "Noviembre 2019")].tail(9).copy()])

    copia = copia.reset_index()
    copia["Ganador"] = ["VOX", "Ciudadanos", "Podemos", "UPL", "XAV", "UPyD", "España Vaciada", "Soria ¡YA!", "PCAS-TC-RC"] * len(mapa_provincia_merged["Elecciones"].unique())
    copia["Segundo"] = ["Ciudadanos", "Podemos", "UPL", "XAV", "UPyD", "VOX", "PCAS-TC-RC", "España Vaciada", "Soria ¡YA!"] * len(mapa_provincia_merged["Elecciones"].unique())
    copia["Municipio"] = copia["Municipio"] + " "
    copia["geometry"] = copia["geometry"].translate(30, 0)
    copia = copia.set_index("Municipio")

    orden = {"Elecciones": ["Noviembre 2011", "Diciembre 2015", "Junio 2016", "Abril 2019", "Noviembre 2019"]}
    mapa_provincia_merged = pd.concat([mapa_provincia_merged, copia])

    fig_provincia = px.choropleth_mapbox(mapa_provincia_merged, geojson=mapa_provincia_merged.geometry,
                                         locations=mapa_provincia_merged.index, color=ganador,
                                         color_discrete_map={"PSOE": "red",
                                                             "PP": "blue",
                                                             "VOX": 'green',
                                                             "Podemos": "purple",
                                                             "Ciudadanos": "orange",
                                                             "UPyD": "hotpink",
                                                             "UPL": "hotpink",
                                                             "XAV": "yellow",
                                                             "IU": "mediumvioletred",
                                                             "España Vaciada": "black",
                                                             "Soria ¡YA!": "black",
                                                             "PCAS-TC-RC": "lightblue",
                                                             "Territorio común (condominio)": "#CEFFEA"},
                                         hover_data=(["Provincia", "Segundo"] if ganador == "Ganador" else ["Provincia", "Ganador"]),
                                         animation_frame="Elecciones",
                                         center=coordenadas,
                                         mapbox_style="open-street-map",
                                         category_orders=orden,
                                         zoom=zoom_arg,
                                         opacity=0.7,
                                         height=750)
    fig_provincia.update_geos(fitbounds="locations", visible=False)

    last_frame_num = int(len(fig_provincia.frames) - 1)
    fig_provincia.layout['sliders'][0]['active'] = last_frame_num
    fig_provincia = go.Figure(data=fig_provincia['frames'][last_frame_num]['data'],
                              frames=fig_provincia['frames'], layout=fig_provincia.layout)
    fig_provincia.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1200

    for button in fig_provincia.layout.updatemenus[0].buttons:
        button['args'][1]['frame']['redraw'] = True

    for k in range(len(fig_provincia.frames)):
        fig_provincia.frames[k]['layout'].update(title_text=('Primera' if ganador == "Ganador" else 'Segunda') + ' fuerza en cada municipio de ' + provincia_elegida + ' en las elecciones ' + tipo_elecciones.lower() + ' de ' + fig_provincia.frames[k].name)

    fig_provincia.update_layout(
        title_text=('Primera' if ganador == "Ganador" else 'Segunda') + ' fuerza en cada municipio de ' + provincia_elegida + ' en las elecciones ' + tipo_elecciones.lower() + ' de ' + fig_provincia.frames[-1].name,
        title=dict(x=0.5),
        plot_bgcolor="rgb(245, 245, 245)",
        margin={"r": 5, "t": 35, "l": 5, "b": 10},
        showlegend=False,
        hoverlabel=dict(align="left", bgcolor="forestgreen", font_family="Rockwell", font_size=14))
    fig_provincia.update_traces(marker=dict(line=dict(color='grey')))

    return fig_provincia


@st.cache_data(suppress_st_warning=True, show_spinner=False)
def pintar_mapa_partidos(mapa_provincia_merged, zoom_arg, coordenadas, partido):
    """
        Devuelve el mapa de Castilla y León o de una de sus provincias con una escala de color continuo. Esta escala
        de color hará referencia al porcentaje de voto de un partido elegido o al porcentaje de participación.

        Parámetros
        ----------
        mapa_provincia_merged: geopandas
        zoom_arg: int
        coordenadas: dict
        partido: str

        """
    orden = {"Elecciones": ["Noviembre 2011", "Diciembre 2015", "Junio 2016", "Abril 2019", "Noviembre 2019"]}
    minimo_color_votos = 0
    maximo_color_votos = 50
    hover_data = ["Provincia", "Censo electoral", partido, partido + " %"]
    color_axis_colorbar = {'title': ' % Votos',
                           'tickvals': ["10", "20", "30", "40", "50"],
                           'ticktext': ["10", "20", "30", "40", "50 o más"]}

    if partido == "PSOE":
        color = "Reds"
        bgcolor = "indianred"
    elif partido == "PP":
        color = "Blues"
        bgcolor = "lightblue"
    elif partido == "VOX":
        color = "Greens"
        bgcolor = "forestgreen"
    elif partido == "Podemos":
        color = "Purples"
        bgcolor = "rebeccapurple"
    elif partido == "Ciudadanos":
        color = "Oranges"
        bgcolor = "orangered"
    elif partido == "UPL":
        st.warning("El partido UPL sólo se presenta en las circunscripciones de León, Zamora y Salamanca")
        color = "pinkyl"
        bgcolor = "deeppink"
    elif partido == "XAV":
        st.warning("El partido XAV (Por Ávila) sólo se presenta en la circunscripción de Ávila (y Valladolid en 2022)")
        color = "YlOrBr"
        bgcolor = "yellow"
    elif (partido == "España Vaciada") | (partido == "Soria ¡YA!"):
        color = "Greys"
        bgcolor = "black"
    else:
        color = "turbid"
        bgcolor = "floralwhite"
        minimo_color_votos = 40
        maximo_color_votos = 90
        hover_data = ["Provincia", "Censo electoral", "Votos emitidos", partido + " %"]
        color_axis_colorbar = {'title': ' % Votos',
                               'tickvals': ["40", "50", "60", "70", "80", "90"],
                               'ticktext': ["40", "50", "60", "70", "80", "90 o más"]}

    fig_provincia = px.choropleth_mapbox(mapa_provincia_merged, geojson=mapa_prov_merged.geometry,
                                         locations=mapa_provincia_merged.index, color=partido + " %",
                                         animation_frame="Elecciones",
                                         hover_data=hover_data,
                                         color_continuous_scale=color,
                                         center=coordenadas,
                                         category_orders=orden,
                                         mapbox_style="open-street-map",
                                         opacity=0.75,
                                         zoom=zoom_arg,
                                         height=750)
    fig_provincia.update_geos(fitbounds="locations", visible=False)
    fig_provincia.update_coloraxes(cmin=minimo_color_votos, cmax=maximo_color_votos)

    if len(mapa_provincia_merged["Elecciones"].unique()) > 1:
        last_frame_num = int(len(fig_provincia.frames) - 1)
        fig_provincia.layout['sliders'][0]['active'] = last_frame_num
        fig_provincia = go.Figure(data=fig_provincia['frames'][last_frame_num]['data'],
                                  frames=fig_provincia['frames'], layout=fig_provincia.layout)
        fig_provincia.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1200

        for button in fig_provincia.layout.updatemenus[0].buttons:
            button['args'][1]['frame']['redraw'] = True

        for k in range(len(fig_provincia.frames)):
            fig_provincia.frames[k]['layout'].update(
                title_text='Resultados de ' + partido + ' en ' + provincia_elegida + ' en las elecciones ' + tipo_elecciones.lower() + ' de ' +
                           fig_provincia.frames[k].name)
    else:
        pass


    fig_provincia.update_layout(
        title_text='Resultados de ' + partido + ' en ' + provincia_elegida + ' en las elecciones ' + tipo_elecciones.lower() + ' de ' + ("2022" if tipo_elecciones == "Autonómicas" else "Noviembre 2019"),
        title=dict(x=0.5),
        margin={"r": 5, "t": 35, "l": 5, "b": 10},
        hoverlabel=dict(align="left", bgcolor=bgcolor, font_family="Rockwell", font_size=14),
        coloraxis_colorbar=color_axis_colorbar)

    return fig_provincia


mapa_cyl = "au.muni_cyl_recintos_comp.shp"
mapa_cyl = gpd.read_file(mapa_cyl)
#mapa_cyl.drop(["nombre", "c_muni_id", "superf", "inspireid"], axis=1, inplace=True)

cyl_elecciones = seleccionar_elecciones(provincia_elegida, tipo_elecciones)
mapa_prov, zoom_prov, coord_prov = seleccionar_provincia(mapa_cyl, provincia_elegida)
mapa_prov_merged = mapa_prov.merge(cyl_elecciones, on="codmun")
mapa_prov_merged = mapa_prov_merged.set_index("Municipio")
mapa_prov_merged = mapa_prov_merged.sort_values(by="Elecciones")

if modo == "Ganador de las elecciones":
    mapa_final = pintar_mapa_ganador(mapa_prov_merged, zoom_prov, coord_prov, tipo_elecciones)
    st.plotly_chart(mapa_final, use_container_width=True, sharing="streamlit")
else:
    mapa_final = pintar_mapa_partidos(mapa_prov_merged, zoom_prov, coord_prov, partido_elegido)
    st.plotly_chart(mapa_final, use_container_width=True, sharing="streamlit")
st.markdown("""
    <div style="text-align:right">©Junta de Castilla y León</div>
""", unsafe_allow_html=True)

