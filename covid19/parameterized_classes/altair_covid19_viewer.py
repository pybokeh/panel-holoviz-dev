from datetime import date
from datetime import datetime
from datetime import timedelta
import altair as alt
import panel as pn
import param
import pandas as pd

class Covid19ViewerUS(param.Parameterized):
    """ A Panel parameterized class for creating COVID-19 dashboard for US states only """

    # Read source data so that we can create valid values for our selection widget, instead of creating
    # hard-coded values, sacrificing a little bit of performance for less maintainenance
    url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/' + \
          'master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_confirmed_US.csv'
    df = pd.read_csv(url).query("Province_State not in(['Grand Princess', 'Diamond Princess'])")
    states_provinces = df['Province_State'].unique().tolist()

    # Create widget to select one or more states
    state_province = param.ListSelector(default=['Ohio'], objects=states_provinces, label='State:')
    # Create date picker widget.  Usually COVID19 data is a day behind
    covid19_date = param.Date(default=date.today() + timedelta(days=-1), bounds=(date(2019, 1, 1), date.today() + timedelta(days=-1)), label='Data as of:')
    # Create widget to choose # of confirmed cases or # of deaths
    confirmed_deaths = param.Selector(default='Confirmed Cases', objects=['Confirmed Cases', 'Deaths'], label='Confirmed Cases or Deaths:')
    # Create widget to choose linear or log scaling
    ylog = param.Selector(default='linear', objects=['linear', 'symlog'], label='Scale:')
    
    @param.depends('confirmed_deaths')
    def getData(self):
        """ Function to obtain data for COVID-19 confirmed cases or COVID-19 deaths """

        if self.confirmed_deaths == 'Confirmed Cases':
            url = 'https://raw.githubusercontent.com/CSSEGISandData/' + \
                  'COVID-19/master/csse_covid_19_data/csse_covid_19_time_series/'+ \
                  'time_series_covid19_confirmed_US.csv'
        else:
            url = 'https://raw.githubusercontent.com/CSSEGISandData/COVID-19/' + \
                  'master/csse_covid_19_data/csse_covid_19_time_series/time_series_covid19_deaths_US.csv'
        
        # If making visualizations at county level, then the FIPS data needs to be fixed - it needs to have leading zeros
        df = pd.read_csv(url, converters={'FIPS': lambda x: int(float(x)) if x != '' else x}).query("FIPS != ''")
        df['FIPS'] = df['FIPS'].astype('str').str.zfill(5)
        if 'Population' in df.columns:
            df.drop(columns='Population', inplace=True)
        
        return df
    
    def dfByState(self):
        """ Function to create dataframe consisting of counts by US states that will be plotted using Altiar
            Altair requires the data to be in "long format"
        """

        df_by_state = (self.getData()
                       .drop(columns=['UID', 'iso2', 'iso3', 'code3', 'FIPS', 'Admin2', 'Country_Region', 'Lat', 'Long_', 'Combined_Key'])
                       .groupby('Province_State').agg('sum')
                       .transpose()
                       .reset_index()
                       .melt(id_vars='index', var_name='State_Province', value_name='Qty_Confirmed')
                       .rename(columns={'index': 'Date'})
                       .set_index('Date')
                      )
        df_by_state.index = [datetime.strptime(date, '%m/%d/%y') for date in df_by_state.index]
        
        return df_by_state
    
    @param.depends('covid19_date', 'state_province', 'confirmed_deaths', 'ylog')
    def plotAltairLineChart(self):
        """ Function to out Altair line chart """
        
        # Date that will be used to indicate "Data as of user chosen date"
        iso_date = self.covid19_date.strftime('%Y-%m-%d')
        # Altair charting API only charts dataframe columns, not index, so need to apply reset_index()
        alt_chart = alt.Chart(self.dfByState()[:iso_date].query("State_Province in(@self.state_province)")
                                                         .reset_index()
                                                         .rename(columns={'index': 'Date'})
                             ).mark_line().encode(
                                           x=alt.X(title='Date', field='Date', type='temporal'),
                                           y=alt.Y(title='# of ' + self.confirmed_deaths, field='Qty_Confirmed', 
                                                   type='quantitative', scale=alt.Scale(type=self.ylog)
                                                  ),
                                           color=alt.Color(field='State_Province', type='nominal',
                                                           legend=alt.Legend(title="State/Province")
                                                          ),
                                           tooltip=[alt.Tooltip(field='State_Province', type= 'nominal'),
                                                    alt.Tooltip(field='Qty_Confirmed', type= 'quantitative'),
                                                    alt.Tooltip(field='Date', type= 'temporal')
                                                   ]
                                          )
        # https://github.com/altair-viz/altair/issues/1812
        # Currently there is a bug where the dates shown in the Altair tooltip are off by one day
        # https://github.com/holoviz/panel/issues/1303
        alt_chart = alt_chart + alt_chart.mark_point(size=100, opacity=0, tooltip=alt.TooltipContent("data"))
        
        return alt_chart.properties(
                title='COVID-19 ' + self.confirmed_deaths,
                width=700,
                height=400
               )