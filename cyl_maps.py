import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import geopandas as gpd
import pyproj
from PIL import Image
import streamlit as st


img = Image.open("CyL.png")
st.set_page_config(page_title="CyL en mapas", page_icon=img)

st.markdown(
        f""" <style>.reportview-container .main .block-container{{
        max-width: {1500}px;
        padding-top: {1}rem;
        padding-right: {6}rem;
        padding-left: {6}rem;
        padding-bottom: {0}rem;
    }},
    .sidebar .sidebar-content {{
                width: 200px;
</style>
""", unsafe_allow_html=True)

st.markdown("""
    <div style="background-color:#FF815F;padding:0px">
    <h1 style="color:#FFFFFF ;text-align:center;">Castilla y León en mapas</h1>
    </div>
""", unsafe_allow_html=True)

st.markdown("<h4 style='text-align: center; '>A continuación se presentan en forma de mapas interactivos los resultados"
            "de las 3 últimas citas electorales en Castilla y Léon.</h4>",
            unsafe_allow_html=True)

st.markdown("<h5 style='text-align: center; '>"
            "¿Recuerdas lo que ocurrió en tu municipio en anteriores elecciones? ¡Descúbrelo en el mapa!</h5>",
            unsafe_allow_html=True)

modo = st.sidebar.radio(label="Elija el modo de visualización",
                        options=['% de voto por partidos', 'Ganador de las elecciones'],
                        help="Podrá visualizar, por un lado, mapas correspondientes al resultado de cada partido"
                             " en cada provincia. También tiene la opción de ver cada municipio coloreado"
                             " según el partido ganador, o el segundo más votado")

c1, c2 = st.columns((1, 1))

with c1:
    provincia_elegida = st.selectbox('Elija qué provincia desea visualizar:',
                                     ('Castilla y León', 'Ávila', 'Burgos', 'León', 'Palencia',
                                      'Salamanca', 'Segovia', 'Soria', 'Valladolid', 'Zamora'))

if modo == 'Ganador de las elecciones':
    with c2:
        ganador = st.selectbox('Cada municipio tendrá el color del:',
                               ('Ganador', 'Segundo'))
else:
    with c2:
        partido_elegido = st.selectbox('Elija un partido o la participación electoral:',
                                       ('Participación', 'PP', 'PSOE', 'VOX', 'Podemos', 'Ciudadanos', 'UPL', 'XAV',
                                        'UPyD', 'CDS'))


@st.cache(show_spinner=False)
def seleccionar_elecciones(cyl_datos, partido, provincia):
    """
    Selecciona el archivo de datos que contiene los datos de las elecciones elegidas por el usuario

    Parámetros
    ----------
    elecciones: str
    """

    if (partido == "VOX") | (partido == "Ciudadanos") | (partido == "Podemos"):
        cyl_datos = cyl_datos[cyl_datos["Año"] >= 2014]
    elif (partido == "UPL") & (provincia == "León"):
        cyl_datos = cyl_datos[cyl_datos["Año"] >= 1987]
    elif (partido == "UPL") & (provincia == "Zamora"):
        cyl_datos = cyl_datos[cyl_datos["Año"] >= 2003]
    elif (partido == "UPL") & (provincia == "Salamanca"):
        cyl_datos = cyl_datos[(cyl_datos["Año"] == 1987) & (cyl_datos["Año"] == 2019)]
    elif partido == "XAV":
        cyl_datos = cyl_datos[cyl_datos["Año"] == 2019]
    elif partido == "UPyD":
        cyl_datos = cyl_datos[(cyl_datos["Año"] == 2011) & (cyl_datos["Año"] == 2015)]
    elif partido == "CDS":
        cyl_datos = cyl_datos[(cyl_datos["Año"] == 1983) | (cyl_datos["Año"] == 1987) | (cyl_datos["Año"] == 1991) | (cyl_datos["Año"] == 1999) | (cyl_datos["Año"] == 2003)]

    return cyl_datos


@st.cache(show_spinner=False)
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

        mapa_provincia = mapa[mapa["c_prov_id"] == codigo_provincia]

    mapa_provincia.to_crs(pyproj.CRS.from_epsg(4326), inplace=True)
    mapa_provincia["codmun"] = mapa_provincia["codmun"].astype(int)

    return mapa_provincia, zoom_provincia, center_provincia


@st.cache(suppress_st_warning=True, show_spinner=False)
def pintar_mapa_ganador(mapa_provincia_merged, zoom_arg, coordenadas):
    """
    Devuelve el mapa de Castilla y León o de una de sus provincias con cada municipio del color del partido ganador
    de las elecciones elegidas por el usuario

    Parámetros
    ----------
    mapa_provincia_merged: geopandas
    zoom_arg: int
    coordenadas: dict
    """

    fig_provincia = px.choropleth_mapbox(mapa_provincia_merged, geojson=mapa_provincia_merged.geometry,
                                         locations=mapa_provincia_merged.index, color=ganador,
                                         color_discrete_map={"PSOE": "red",
                                                             "PP": "blue",
                                                             "VOX": 'green',
                                                             "Podemos": "purple",
                                                             "Ciudadanos": "orange",
                                                             "UPL": "brown",
                                                             "Por Ávila": "black",
                                                             "CDS": "green",
                                                             "IU": "indianred",
                                                             "Territorio común (condominio)": "#CEFFEA"},
                                         hover_data=(["Provincia", "Segundo"] if ganador == "Ganador" else ["Provincia", "Ganador"]),
                                         animation_frame="Año",
                                         center=coordenadas,
                                         mapbox_style="open-street-map",
                                         zoom=zoom_arg,
                                         opacity=0.7,
                                         height=600)
    fig_provincia.update_geos(fitbounds="locations", visible=False)

    last_frame_num = int(len(fig_provincia.frames) - 1)
    fig_provincia.layout['sliders'][0]['active'] = last_frame_num
    fig_provincia = go.Figure(data=fig_provincia['frames'][last_frame_num]['data'],
                              frames=fig_provincia['frames'], layout=fig_provincia.layout)
    fig_provincia.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1200

    fig_provincia.update_layout(
        title_text=('Primera' if ganador == "Ganador" else 'Segunda') + ' fuerza en cada municipio de ' + provincia_elegida,
        plot_bgcolor="rgb(245, 245, 245)",
        margin={"r": 5, "t": 35, "l": 5, "b": 10},
        showlegend=False,
        hoverlabel=dict(align="left", bgcolor="forestgreen", font_family="Rockwell", font_size=14))
    fig_provincia.update_traces(marker=dict(line=dict(color='grey')))

    return fig_provincia

@st.cache(suppress_st_warning=True, show_spinner=False)
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

    minimo_color_votos = 0
    maximo_color_votos = 50
    hover_data = ["Provincia", "Censo", partido, partido + " %"]
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
        st.warning("El partido XAV (Por Ávila) sólo se presenta en la circunscripción de Ávila")
        color = "Greys"
        bgcolor = "darkgray"
    elif partido == "CDS":
        color = "Greens"
        bgcolor = "forestgreen"
    else:
        color = "turbid"
        bgcolor = "floralwhite"
        minimo_color_votos = 40
        maximo_color_votos = 90
        hover_data = ["Provincia", "Censo", "Votos emitidos", partido + " %"]
        color_axis_colorbar = {'title': ' % Votos',
                               'tickvals': ["40", "50", "60", "70", "80", "90"],
                               'ticktext': ["40", "50", "60", "70", "80", "90 o más"]}

    fig_provincia = px.choropleth_mapbox(mapa_provincia_merged, geojson=mapa_prov_merged.geometry,
                                         locations=mapa_provincia_merged.index, color=partido + " %",
                                         animation_frame="Año",
                                         hover_data=hover_data,
                                         color_continuous_scale=color,
                                         center=coordenadas,
                                         mapbox_style="open-street-map",
                                         opacity=0.75,
                                         zoom=zoom_arg,
                                         height=750)
    fig_provincia.update_geos(fitbounds="locations", visible=False)
    fig_provincia.update_coloraxes(cmin=minimo_color_votos, cmax=maximo_color_votos)

    last_frame_num = int(len(fig_provincia.frames) - 1)
    fig_provincia.layout['sliders'][0]['active'] = last_frame_num
    fig_provincia = go.Figure(data=fig_provincia['frames'][last_frame_num]['data'],
                              frames=fig_provincia['frames'], layout=fig_provincia.layout)
    fig_provincia.layout.updatemenus[0].buttons[0].args[1]["frame"]["duration"] = 1200

    fig_provincia.update_layout(
        title_text='Resultados de ' + partido + ' en ' + provincia_elegida,
        title=dict(x=0.5),
        margin={"r": 5, "t": 35, "l": 5, "b": 10},
        hoverlabel=dict(align="left", bgcolor=bgcolor, font_family="Rockwell", font_size=14),
        coloraxis_colorbar=color_axis_colorbar)

    return fig_provincia



cyl_resultados = pd.read_excel("CyL autonómicas.xlsb")

mapa_cyl = "au.muni_cyl_recintos_comp.shp"
mapa_cyl = gpd.read_file(mapa_cyl)
mapa_cyl.drop(["nombre", "c_muni_id", "superf", "inspireid"], axis=1, inplace=True)

cyl_elecciones = seleccionar_elecciones(cyl_resultados, partido_elegido, provincia_elegida)
mapa_prov, zoom_prov, coord_prov = seleccionar_provincia(mapa_cyl, provincia_elegida)
mapa_prov_merged = mapa_prov.merge(cyl_elecciones, on="codmun")
mapa_prov_merged = mapa_prov_merged.set_index("Municipio")
mapa_prov_merged = mapa_prov_merged.sort_values(by="Año")

if modo == "Ganador de las elecciones":
    mapa_final = pintar_mapa_ganador(mapa_prov_merged, zoom_prov, coord_prov)
    st.plotly_chart(mapa_final, use_container_width=True, sharing="streamlit")
else:
    mapa_final = pintar_mapa_partidos(mapa_prov_merged, zoom_prov, coord_prov, partido_elegido)
    st.plotly_chart(mapa_final, use_container_width=True, sharing="streamlit")
st.markdown("""
    <div style="text-align:right">©Junta de Castilla y León</div>
""", unsafe_allow_html=True)
