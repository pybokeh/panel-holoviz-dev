import altair_covid19_viewer
import panel as pn

us_class = altair_covid19_viewer.Covid19ViewerUS(name='COVID-19 US Only')

us_app = pn.Row(pn.Column(pn.Param(us_class.param.state_province, height=100, widgets={'state_province': pn.widgets.MultiChoice}),
                 pn.Param(us_class.param.covid19_date, widgets={'covid19_date': pn.widgets.DatePicker}),
                 pn.Param(us_class.param.confirmed_deaths),
                 pn.Param(us_class.param.ylog)
                ),
                us_class.plotAltairLineChart,
                height=500
         )

us_app.show(host='localhost', port=8889, websocket_origin='localhost:8889', open=False)