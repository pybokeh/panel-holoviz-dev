import altair_covid19_viewer
import panel as pn

us = altair_covid19_viewer.Covid19ViewerUS(name='COVID-19 US Only')
_global = altair_covid19_viewer.Covid19ViewerGlobal(name='COVID-19 Globally')

us_app = pn.Column(pn.Param(us.param.covid19_date, widgets={'covid19_date': pn.widgets.DatePicker}),
                   pn.Param(us.param.state_province, height=100, widgets={'state_province': pn.widgets.MultiChoice}),
                   pn.Param(us.param.confirmed_deaths),
                   pn.Param(us.param.ylog),
                   pn.Row(us.plotAltairLineChart, us.hvtableByState, us.hvtableByCounties),
                   us.plotlyChoropleth
                  )

global_app = pn.Column(pn.Param(_global.param.covid19_date, widgets={'covid19_date': pn.widgets.DatePicker}),
                   pn.Param(_global.param.country, height=100, widgets={'country': pn.widgets.MultiChoice}),
                   pn.Param(_global.param.confirmed_deaths),
                   pn.Param(_global.param.ylog),
                   pn.Row(_global.plotAltairLineChart, _global.hvtableByDate, min_width=1000, sizing_mode='stretch_width')
                  ) 

#us_app.show(host='localhost', port=8889, websocket_origin='localhost:8889', open=False)

pn.serve({'By_Country': global_app, 'US_Only': us_app}, port=8890, websocket_origin='localhost:8890', show=False)