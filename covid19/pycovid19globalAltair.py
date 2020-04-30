# Currently there is a bug where the dates shown in the Altair tooltip are off by one day
# https://github.com/holoviz/panel/issues/1303
from datetime import date
from datetime import datetime
from datetime import timedelta
from typing import TypeVar, List
import altair as alt
import hvplot.pandas
import pandas as pd
import panel as pn
# These are related to optional type annotations
Altair = TypeVar('altair.vegalite.v4.api.LayerChart')
DataFrame = TypeVar('pd.core.frame.DataFrame')
Date = TypeVar('datetime.date')
DatePicker = TypeVar('panel.widgets.input.DatePicker')
DateTimeIndex = TypeVar('pd.core.indexes.datetimes.DatetimeIndex')
PanelColumn = TypeVar('pn.layout.Column')
PanelRow = TypeVar('pn.layout.Row')
MultiChoice = TypeVar('panel.widgets.select.MultiChoice')
RangeIndex = TypeVar('pandas.core.indexes.range.RangeIndex')
Select = TypeVar('panel.widgets.select.Select')
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

url: str = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
df: DataFrame = pd.read_csv(url)

# Create input widgets: date widget and 2 selection widgets
# There is bug in the date widget in version 0.9.3: https://github.com/holoviz/panel/issues/1173
# Manually fixed the bug by modifying input.py source file
# Make default date yesterday (today minus 1 day) since COVID-19 data is usually 1 day behind
countries_list: List[str] = df['Country/Region'].unique().tolist()
covid19_date: DatePicker = pn.widgets.DatePicker(name='Date:', value=(date.today() + timedelta(days=-1)),
                            width=200,
                            css_classes=['grey-theme']
                           )
country: MultiChoice = pn.widgets.MultiChoice(name='Country:', value=['US'], options=countries_list)
confirmed_deaths: Select = pn.widgets.Select(name='Confirmed Cases or Deaths:', value='Confirmed Cases',
                            options=['Confirmed Cases', 'Deaths'],
                            width=200, css_classes=['grey-theme']
                           )
ylog = pn.widgets.Select(name='Scaling: linear/symlog', value='linear', options=['linear', 'symlog'], 
        width=200, css_classes=['grey-theme']
       )

@pn.depends(covid19_date.param.value, confirmed_deaths.param.value, country.param.value, ylog.param.value)
def covid19TimeSeriesByCountry(covid19_date: Date, confirmed_deaths: str, country: List[str]=['US'], ylog: bool=False) -> PanelRow:
    """Function that returns a Panel dashboard displaying confirmed COVID-19 cases
    It is using Panel's "Reactive functions" API: https://panel.holoviz.org/user_guide/APIs.html
    Parameters
    ----------
    covid19_date : Date
        End date of data you wish to obtain up to
    country : List[str]
        One or more countries for which you would like to obtain data for (default='US')
    confirmed_deaths : str
        Option to choose # of confirmed cases or # of deaths from Covid-19
    ylog: bool
        Whether or not to apply log scaling to y-axis.  Default is False
    Returns
    -------
    Panel object
    """
    
    iso_date: str = covid19_date.strftime('%Y-%m-%d')

    # Source of COVID-19 data
    if confirmed_deaths == 'Confirmed Cases':
        url: str = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
    else:
        url: str = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_global.csv'
    df: DataFrame = pd.read_csv(url)

    df_countries: DataFrame = (df.drop(columns=['Province/State', 'Lat', 'Long'])
                                 .groupby('Country/Region').agg('sum')
                                 .sort_values(by=df.columns[-1], ascending=False)
                                 .transpose()
                                 .reset_index()
                                 .melt(id_vars='index', value_name='Qty')
                                 .rename(columns={'index': 'Date', 'Country/Region': 'Country_Region'})
                                 .set_index('Date')
                              )

    df_countries.index: DateTimeIndex = [datetime.strptime(date, '%m/%d/%y') for date in df_countries.index]

    # Convert data to "wide format" since hvplot does not work with "long format"
    df_countries_wide = df_countries.pivot(columns='Country_Region', values='Qty')

    alt_chart: Altair = alt.Chart(df_countries[: iso_date].query("Country_Region in(@country)")
                         .reset_index()
                         .rename(columns={'index': 'Date'})
                        ).mark_line().encode(
                         x=alt.X(title='Date', field='Date', type='temporal'),
                         y=alt.Y(title='# of ' + confirmed_deaths, field='Qty', type='quantitative', scale=alt.Scale(type=ylog)),
                         color=alt.Color(field='Country_Region', type='nominal', legend=alt.Legend(title="Country/Region")),
                         tooltip=[alt.Tooltip(field='Country_Region', type= 'nominal'),
                                  alt.Tooltip(field='Qty', type= 'quantitative'),
                                  alt.Tooltip(field='Date', type= 'temporal')
                                 ]
                        )
    # https://github.com/altair-viz/altair/issues/1812
    alt_chart: Altair = alt_chart + alt_chart.mark_point(size=100, opacity=0, tooltip=alt.TooltipContent("data"))

    # If only one country is selected, then also provide a data table containing counts by date
    if len(country) == 1:
        panel_app: PanelRow = pn.Row(
                                 # Add Altair chart
                                 alt_chart.properties(
                                  title='COVID-19 ' + confirmed_deaths,
                                  width='container',  # Have to use 'container' option, otherwise, layout is 
                                  height=400
                                 ),
                                 # Add hvplot table using data in wide format
                                 df_countries_wide[:iso_date].loc[:, country]
                                 .sort_values(by=df_countries_wide[:iso_date].loc[:, country].columns[0], ascending=False)
                                 .merge(df_countries_wide[:iso_date].loc[:, country].sort_values(by=df_countries_wide[:iso_date]
                                        .loc[:, country].columns[0], ascending=False
                                       )
                                 .diff(), how='inner', left_index=True, right_index=True)
                                 .reset_index()
                                 .rename(columns={'index': 'Date', f'{country[0]}_x': 'Cum. Qty', f'{country[0]}_y': 'Difference'})
                                 .hvplot.table(sortable=True,
                                               selectable=True,
                                               width=300,
                                               height=500
                                              )  
                              )
    # Else provide just the Altair line chart
    else:
        panel_app: PanelRow = pn.Row(alt_chart.properties(
                                       title='COVID-19 ' + confirmed_deaths,
                                       width=700,
                                       height=400
                                    )
                              )

    return panel_app

global_app: PanelColumn = pn.Column(
                           covid19_date,
                           country,
                           confirmed_deaths,
                           ylog,
                           covid19TimeSeriesByCountry,
                           sizing_mode='stretch_width',
                           max_width=1200
                          )