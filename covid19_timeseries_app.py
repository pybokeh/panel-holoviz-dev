from datetime import date
from datetime import datetime
from datetime import timedelta
from typing import TypeVar
import hvplot.pandas
import pandas as pd
import panel as pn
import platform
DataFrame = TypeVar('pd.core.frame.DataFrame')
Date = TypeVar('datetime.date')
DateTimeIndex = TypeVar('pd.core.indexes.datetimes.DatetimeIndex')
Panel = TypeVar('pn.layout.Row')

# Create a list of countries to be used in making a selection widget
url = 'https://www.soothsawyer.com/wp-content/uploads/2020/03/time_series_19-covid-Confirmed.csv'
df = pd.read_csv(url)
countries = df['Country/Region'].unique().tolist()

# Create input widgets: date widget and 2 selection widgets
# There is bug in the date widget in version 0.9.3: https://github.com/holoviz/panel/issues/1173
# Manually fixed the bug by modifying input.py source file
# Make default date yesterday (today minus 1 day) since COVID-19 data is usually 1 day behind
covid19_date = pn.widgets.DatePicker(name='Date:', value=(date.today() + timedelta(days=-1)))
country = pn.widgets.Select(name='Country:', options=countries, value='US')
top = pn.widgets.Select(name='Top N Province/State:', options=[5, 10], value=5)

@pn.depends(covid19_date.param.value, country.param.value, top.param.value)
def covid19TimeSeries(covid19_date: Date, country: str='US', top: int=5) -> Panel:
    """Function that returns a Panel dashboard displaying confirmed COVID-19 cases
    SOURCE of data:
    https://www.soothsawyer.com/wp-content/uploads/2020/03/time_series_19-covid-Confirmed.csv
    It is using Panel's "Reactive functions" API: https://panel.holoviz.org/user_guide/APIs.html

    Parameters
    ----------
    covid19_date : Date
        End date of data you wish to obtain up to
    country : str
        Country for which you would like to obtain data for (default='US')
    top : int
        The Top N provinces or states for which you are requesting to plot (default=5)

    Returns
    -------
    Panel object
    """
    
    iso_date: str = covid19_date.strftime('%Y-%m-%d')
    
    if 'Linux' in platform.system():
        data_date: str = date.fromisoformat(iso_date).strftime('%-m/%-d/%Y')# Tag
    elif 'MacOS' in platform.system():
        data_date: str = date.fromisoformat(iso_date).strftime('%-m/%-d/%Y')
    elif 'Windows' in platform.system():
        data_date: str = date.fromisoformat(iso_date).strftime('%#m/%#d/%Y')

    # Source of COVID-19 data        
    url = 'https://www.soothsawyer.com/wp-content/uploads/2020/03/time_series_19-covid-Confirmed.csv'
    df: DataFrame = pd.read_csv(url)

    if 'US' in country:
        df: DataFrame = df.fillna({'Province/State': ''})
        df: DataFrame = df[(df['Country/Region'] == country) & (~df['Province/State'].str.contains(','))]
        df: DataFrame = df.sort_values(by=data_date, ascending=False).drop(columns=['Country/Region', 'Lat', 'Long'])
    elif country in['Australia', 'Canada', 'China', 'Denmark', 'France', 'Netherlands', 'United Kingdom']:
        df: DataFrame = df.fillna({'Province/State': ''})
        df: DataFrame = df[df['Country/Region'] == country]
        df: DataFrame = df.sort_values(by=data_date, ascending=False).drop(columns=['Country/Region', 'Lat', 'Long'])
    else:
        df: DataFrame = df[df['Country/Region'] == country]
        df: DataFrame = df.sort_values(by=data_date, ascending=False).drop(columns=['Province/State', 'Lat', 'Long'])

    # Transpose and then replace column with 1st row of dataframe 
    df_final: DataFrame = df.transpose()
    df_final: DataFrame = df_final.rename(columns=df_final.iloc[0]).drop(df_final.index[0])

    # Make index an actual datetime data type for easier date filtering 
    df_final.index: DateTimeIndex = [datetime.strptime(date, '%m/%d/%Y') for date in df_final.index]

    # For countries that have provinces or states (except China):
    if country in['Australia', 'Canada', 'Denmark', 'France', 'Netherlands', 'United Kingdom', 'US']:
        panel_app: Panel = pn.Row(df_final['2020-03-10':data_date].iloc[:, range(top)].hvplot(
                               title=f'{country}: Top {top} Provinces/States with COVID-19',
                               width=800,
                               height=600,
                               ylabel='# of Confirmed Cases',
                               xlabel='Date',
                               legend='bottom',
                               yformatter='%d'
                               ),
                               df_final['2020-03-10':data_date].iloc[:, range(top)].hvplot.table(
                                                                                      sortable=True,
                                                                                      selectable=True,
                                                                                      width=600
                                                                                  )
                           )
    elif 'China' in country:
        panel_app: Panel = pn.Row(df_final[:data_date].iloc[:, range(top)].hvplot(
                               title=f'{country}: Top {top} Provinces/States with COVID-19',
                               width=800,
                               height=600,
                               ylabel='# of Confirmed Cases',
                               xlabel='Date',
                               legend='bottom',
                               yformatter='%d'
                               ),
                               df_final[:data_date].iloc[:, range(top)].hvplot.table(
                                                                       sortable=True,
                                                                       selectable=True,
                                                                       width=600
                                                                   )
                           )
    else:
        panel_app: Panel = pn.Row(df_final[:data_date].hvplot(
                               title=f'{country}: Confirmed Cases with COVID-19',
                               width=800,
                               height=600,
                               ylabel='# of Confirmed Cases',
                               xlabel='Date',
                               legend='bottom',
                               yformatter='%d'
                               ),
                               df_final[:data_date].hvplot.table(
                                                   sortable=True,
                                                   selectable=True,
                                                   width=600
                                               )
                           )
    
    return panel_app

app = pn.Column(
          covid19_date,
          country,
          top,
          covid19TimeSeries
      )

app.show(host='localhost', port=8890)