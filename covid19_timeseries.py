from datetime import date
from datetime import datetime
from datetime import timedelta
from typing import TypeVar
import hvplot.pandas
import pandas as pd
import panel as pn
import platform
DataFrame = TypeVar('pd.core.frame.DataFrame')
DateTimeIndex = TypeVar('pd.core.indexes.datetimes.DatetimeIndex')
Panel = TypeVar('pn.layout.Row')


def covid19TimeSeries(iso_date: str, top: int=5) -> Panel:
    """ Function that returns a Panel dashboard

    Parameters
    ----------
    iso_date : str
        The date for which the desired data you are requesting in YYYY-MM-DD
    top : int
        The Top N U.S. states for which you are requesting to plot

    Returns
    -------
    Panel object
    """
    
    if 'Linux' in platform.system():
        data_date: str = date.fromisoformat(iso_date).strftime('%-m/%-d/%Y')
    elif 'MacOS' in platform.system():
        data_date: str = date.fromisoformat(iso_date).strftime('%-m/%-d/%Y')
    elif 'Windows' in platform.system():
        data_date: str = date.fromisoformat(iso_date).strftime('%#m/%#d/%Y')

    url = 'https://www.soothsawyer.com/wp-content/uploads/2020/03/time_series_19-covid-Confirmed.csv'
    
    df: DataFrame = pd.read_csv(url)
    df: DataFrame = df.fillna({'Province/State': ''})
    df_us: DataFrame = df[(df['Country/Region'] == 'US') & (~df['Province/State'].str.contains(','))]
    df: DataFrame = df_us.sort_values(by=data_date, ascending=False).drop(columns=['Country/Region', 'Lat', 'Long'])
    
    df_final: DataFrame = df.transpose()
    df_final: DataFrame = df_final.rename(columns=df_final.iloc[0]).drop(df_final.index[0])
    df_final: DataFrame = df_final.drop(columns=['Diamond Princess', 'Grand Princess'])
    
    df_final.index: DateTimeIndex = [datetime.strptime(date, '%m/%d/%Y') for date in df_final.index]
    
    panel_app: Panel = pn.Row(df_final['2020-03-10':].iloc[:, range(top)].hvplot(
                           title='Top 5 U.S. States COVID-19',
                           width=800,
                           height=600,
                           ylabel='# of Confirmed Cases',
                           xlabel='Date',
                           legend='bottom'
                           ),
                           df_final['2020-03-10':].iloc[:, range(5)].hvplot.table(sortable=True, selectable=True, width=600)
                       )
    
    return panel_app


if __name__ == '__main__':
    latest_date = (date.today() + timedelta(days=-1)).strftime("%Y-%m-%d")
    covid19TimeSeries(latest_date).show(host='localhost', port=8889)
