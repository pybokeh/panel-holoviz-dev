from datetime import date
from datetime import datetime
from datetime import timedelta
from typing import TypeVar, List
import hvplot.pandas
import pandas as pd
import panel as pn
# These are related to optional type annotations
DataFrame = TypeVar('pd.core.frame.DataFrame')
Date = TypeVar('datetime.date')
DatePicker = TypeVar('panel.widgets.input.DatePicker')
DateTimeIndex = TypeVar('pd.core.indexes.datetimes.DatetimeIndex')
Panel = TypeVar('pn.layout.Row')
MultiChoice = TypeVar('panel.widgets.select.MultiChoice')
RangeIndex = TypeVar('pandas.core.indexes.range.RangeIndex')
Select = TypeVar('panel.widgets.select.Select')

url: str = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_global.csv'
df: DataFrame = pd.read_csv(url)

# Create input widgets: date widget and 2 selection widgets
# There is bug in the date widget in version 0.9.3: https://github.com/holoviz/panel/issues/1173
# Manually fixed the bug by modifying input.py source file
# Make default date yesterday (today minus 1 day) since COVID-19 data is usually 1 day behind
countries_list: List[str] = df['Country/Region'].unique().tolist()
covid19_date: DatePicker = pn.widgets.DatePicker(name='Date:', value=(date.today() + timedelta(days=-1)))
country: MultiChoice = pn.widgets.MultiChoice(name='Country:', value=['US'],
    options=countries_list)
confirmed_deaths = pn.widgets.Select(name='Confirmed Cases or Deaths:', value='Confirmed Cases', options=['Confirmed Cases', 'Deaths'],
                                     width=200, css_classes=['grey-theme'])
ylog: Select = pn.widgets.Select(name='log-y?', value=False, options=[True, False])

@pn.depends(covid19_date.param.value, confirmed_deaths.param.value, country.param.value, ylog.param.value)
def covid19TimeSeriesByCountry(covid19_date: Date, confirmed_deaths: str, country: List[str]=['US'], ylog: bool=False) -> Panel:
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
                              )

    # Make index an actual datetime data type for easier date filtering.
    # JHU have not been consistent with their year format (YYYY vs YY).
    # Therefore, added try/except clause to account for both formats
    try:
        df_countries.index: RangeIndex = [datetime.strptime(date, '%m/%d/%y') for date in df_countries.index]
    except ValueError as e:
        print("YY year format not detected.  Using YYYY instead.", e)
        df_countries.index: RangeIndex = [datetime.strptime(date, '%m/%d/%Y') for date in df_countries.index]

    # If only one country is selected, then also provide a data table containing counts by date
    if len(country) == 1:
        panel_app: Panel = pn.Row(df_countries[:iso_date].loc[:, country].hvplot(
                               title='COVID-19 ' + confirmed_deaths,
                               logy=ylog,
                               width=700,
                               height=500,
                               ylabel='# of ' + confirmed_deaths,
                               xlabel='Date',
                               legend='bottom',
                               yformatter='%d',
                               grid=True
                              ),
                              df_countries[:iso_date].loc[:, country].sort_values(by=df_countries[:iso_date].loc[:, country].columns[0], ascending=False)
                                                     .merge(df_countries[:iso_date].loc[:, country].sort_values(by=df_countries[:iso_date]
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
    else:
        panel_app: Panel = pn.Row(df_countries[:iso_date].loc[:, country].hvplot(
                               title='COVID-19 ' + confirmed_deaths,
                               logy=ylog,
                               width=700,
                               height=500,
                               ylabel='# of ' + confirmed_deaths,
                               xlabel='Date',
                               legend='bottom',
                               yformatter='%d',
                               grid=True
                              )
                           )

    return panel_app

global_app = pn.Column(
                       covid19_date,
                       country,
                       confirmed_deaths,
                       ylog,
                       covid19TimeSeriesByCountry
                      )