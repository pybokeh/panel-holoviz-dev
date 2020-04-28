# Currently there is a bug where the dates shown in the Altair tooltip are off by one day
# https://github.com/holoviz/panel/issues/1303
from datetime import date
from datetime import datetime
from datetime import timedelta
from typing import TypeVar, List
from urllib.request import urlopen
import altair as alt
import hvplot.pandas
import json
import numpy as np
import pandas as pd
import panel as pn
import platform
import plotly.express as px
# These are related to optional type annotations
Altair = TypeVar('altair.vegalite.v4.api.LayerChart')
DataFrame = TypeVar('pd.core.frame.DataFrame')
Date = TypeVar('datetime.date')
DatePicker = TypeVar('panel.widgets.input.DatePicker')
DateTimeIndex = TypeVar('pd.core.indexes.datetimes.DatetimeIndex')
PanelColumn = TypeVar('pn.layout.Column')
PanelRow = TypeVar('pn.layout.Row')
Plotly = TypeVar('plotly.graph_objs._figure.Figure')
MultiChoice = TypeVar('panel.widgets.select.MultiChoice')
RangeIndex = TypeVar('pandas.core.indexes.range.RangeIndex')
Series = TypeVar('pandas.core.series.Series')
# Related to customizing your Panel's colors
css = '''
.black-theme {
  background-color: black;
  color: white;
}
.grey-theme {
  background-color: #CCD1D1;
  color: black;
}
'''
pn.config.raw_css.clear()
pn.config.raw_css.append(css)

url: str = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv'
df: DataFrame = pd.read_csv(url)

# Create input widgets: date widget, multi-choice, and selection widgets
# Make default date yesterday (today minus 1 day) since COVID-19 data is usually 1 day behind
states_provinces: List[str] = df['Province_State'].unique().tolist()
covid19_date: DatePicker = pn.widgets.DatePicker(name='Date:', value=(date.today() + timedelta(days=-1)),
                                                 width=200, css_classes=['grey-theme']
                                                )
state_province = pn.widgets.MultiChoice(name='State:', value=['Ohio'],
                            options=states_provinces
                           )
confirmed_deaths = pn.widgets.Select(name='Confirmed Cases or Deaths:', value='Confirmed Cases',
                                     options=['Confirmed Cases', 'Deaths'],
                                     width=200, css_classes=['grey-theme']
                                    )
ylog = pn.widgets.Select(name='Scaling: linear/symlog', value='linear', options=['linear', 'symlog'], 
                         width=200,
                         css_classes=['grey-theme']
                        )

@pn.depends(covid19_date.param.value, state_province.param.value, confirmed_deaths.param.value, ylog.param.value)
def covid19TimeSeriesByState(covid19_date: Date, state_province: List[str], confirmed_deaths: List[str], ylog: bool=False) -> PanelColumn:
    """Function that returns a Panel dashboard displaying confirmed COVID-19 cases
    It is using Panel's "Reactive functions" API: https://panel.holoviz.org/user_guide/APIs.html
    Parameters
    ----------
    covid19_date : Date
        End date of data you wish to obtain up to
    state_province : str
        State for which you would like to obtain data for (default='Ohio')
    confirmed_deaths : str
        Option to choose # of confirmed cases or deaths due to COVID-19
    ylog : bool
        To enable log scaling or not on y-axis.  Log scale can be useful to easily discern growth rate.
    Returns
    -------
    Panel object
    """

    # Panel's date widget returns date in ISO-8601 format
    iso_date: str = covid19_date.strftime('%Y-%m-%d')

    # Get geo json data at state county level based on FIPS
    with urlopen('https://raw.githubusercontent.com/plotly/datasets/master/geojson-counties-fips.json') as response:
        geo_data: dict = json.load(response)

    # Source of COVID-19 data
    # To leverage Plotly's choropleth_mapbox function, need to have FIPS as fixed length(n=5) values consisting of leading zeros
    if confirmed_deaths == 'Confirmed Cases':
        url: str = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv'
    else:
        url: str = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv'
    df: DataFrame = pd.read_csv(url, converters={'FIPS': lambda x: int(float(x)) if x != '' else x}).query("FIPS != ''")
    df['FIPS']: Series = df['FIPS'].astype('str').str.zfill(5)
    if 'Population' in df.columns:
        df.drop(columns='Population', inplace=True)

    df_by_state: DataFrame = (df.query("not Province_State in('Diamond Princess', 'Grand Princess')")
                                .drop(columns=['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 'Country_Region', 'Lat', 'Long_', 'Combined_Key'])
                                .groupby('Province_State').agg('sum')
                                .transpose()
                                .reset_index()
                                .melt(id_vars='index', var_name='State_Province', value_name='Qty_Confirmed')
                                .rename(columns={'index': 'Date'})
                                .set_index('Date')
                             )
    df_by_state.index: DateTimeIndex = [datetime.strptime(date, '%m/%d/%y') for date in df_by_state.index]

    # Prepare data for hvplot tables 
    # https://stackoverflow.com/questions/53052914/selecting-non-adjacent-columns-by-column-number-pandas
    df_by_state_ts: DataFrame = df.iloc[:, np.r_[6, 11:df.shape[1]]].groupby('Province_State').agg('sum').transpose()
    df_by_counties: DataFrame = df.query("not Lat==0").iloc[:, [6, 10, -1]]

    # Prepare data for Plotly choropleth map 
    df_choropleth: DataFrame = df.iloc[:, np.r_[4, 5, 6, df.shape[1]-1]]
    df_choropleth: DataFrame = df_choropleth.rename(columns={df_choropleth.columns[3]: 'Confirmed_Cases', 'Admin2': 'County'})
    
    # Initialize plotly choropleth map
    plotly_chart: Plotly = px.choropleth_mapbox(df_choropleth.query("Province_State in@state_province"),
                                        geojson=geo_data,
                                        locations='FIPS',
                                        color='Confirmed_Cases',
                                        color_discrete_map="Viridis",
                                        mapbox_style="carto-positron",
                                        zoom=3.5, center = {"lat": 37.0902, "lon": -95.7129},
                                        opacity=0.5,
                                        hover_name='County',
                                        width=1400,
                                        height=700
                                        )
    plotly_chart.update_layout(margin={"r":0,"t":0,"l":0,"b":0})

    # Initialize altair chart
    alt_chart: Altair = alt.Chart(df_by_state[:iso_date].query("State_Province in(@state_province)")
                                                        .reset_index()
                                                        .rename(columns={'index': 'Date'})
                                 ).mark_line().encode(
                                               x=alt.X(title='Date', field='Date', type='temporal'),
                                               y=alt.Y(title='# of ' + confirmed_deaths, field='Qty_Confirmed', 
                                                  type='quantitative', scale=alt.Scale(type=ylog)
                                                 ),
                                               color=alt.Color(field='State_Province', type='nominal',
                                                      legend=alt.Legend(title="State/Province")
                                                     ),
                                               tooltip=[alt.Tooltip(field='State_Province', type= 'nominal'),
                                                        alt.Tooltip(field='Qty_Confirmed', type= 'quantitative'),
                                                        alt.Tooltip(field='Date', type= 'temporal')]
                                              )
    # https://github.com/altair-viz/altair/issues/1812
    alt_chart: Altair = alt_chart + alt_chart.mark_point(size=100, opacity=0, tooltip=alt.TooltipContent("data"))

    # If only one state is selected, then also provide data tables containing counts by counties, by date, and counties choropleth map
    if len(state_province) == 1:
        # Layout the panel app such that the column will consist of a row of line chart, data table by counties, and data table by state
        # then a plotly choropleth below them 
        panel_app: PanelColumn = pn.Column(pn.Row(
                                           # Add Altair line chart of cum. covid19 cases or deaths
                                           alt_chart.properties(
                                               title='COVID-19 ' + confirmed_deaths,
                                               width='container',  # Have to use 'container' option, otherwise, layout is 
                                               height=400
                                           ),
                                           # A data table of counts by counties
                                           df_by_counties
                                           .query("Province_State == @state_province")
                                           .sort_values(by=df_by_counties.columns[2], ascending=False)
                                           .drop(columns='Province_State', axis='columns')
                                           .rename(columns={'Combined_Key': 'County', 
                                               df_by_counties.columns[2]: 'Qty as of ' + df_by_counties.columns[2]}
                                           )
                                           .hvplot.table(sortable=True,
                                                         selectable=True,
                                                         width=250,
                                                         height=500
                                           ),
                                           # A data table of counts by state with difference between rows
                                           (df_by_state_ts.loc[:, state_province]
                                                          .sort_values(by=state_province, ascending=False)
                                                          .rename(columns={'index': 'Date', state_province[0]: 'Cum. Qty'})
                                           )
                                           .merge((df_by_state_ts.loc[:, state_province]
                                                                 .sort_values(by=state_province, ascending=False)
                                                                 .rename(columns={'index': 'Date', state_province[0]: 'Cum. Qty'})
                                                  ).diff(), how='inner', left_index=True, right_index=True
                                           )
                                           .rename(columns={'Cum. Qty_x':'Cum. Qty', 'Cum. Qty_y': 'Difference'})
                                           .reset_index()
                                           .rename(columns={'index': 'Date'})
                                           .hvplot.table(sortable=True, selectable=True, width=300, height=500),
                                           width=1200,
                                           sizing_mode='stretch_width'
                                     ),
                                     # A plotly choropleth Figure
                                     plotly_chart
                                 )
    # if more than one state is chosen, just provide Altair line chart, as it would not be feasible
    # to try to provide data tables and choropleth maps for several states
    else:
        panel_app: PanelColumn = pn.Column(
                                  pn.Row(
                                   # Add Altair line chart of cum. covid19 cases
                                   alt_chart.properties(
                                       title='COVID-19 ' + confirmed_deaths,
                                       width=700,
                                       height=400
                                   )
                                  )
                                 )

    return panel_app

# Final Panel object, stack Panel components in columnar layout
us_app: PanelColumn = pn.Column(
                         covid19_date,
                         state_province,
                         confirmed_deaths,
                         ylog,
                         covid19TimeSeriesByState
                      )