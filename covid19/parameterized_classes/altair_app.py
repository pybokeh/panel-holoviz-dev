from altair_covid19_viewer import Covid19ViewerUS
import panel as pn

#us_app.show(host='localhost', port=8889, websocket_origin='localhost:8889', open=False)

#pn.serve({'By_Country': global_app, 'US_Only': us_app}, port=8890, websocket_origin='localhost:8890', show=False)

app = Covid19ViewerUS(name='COVID-19 US Only')

panel_app = pn.Row(pn.Column(pn.Param(app.param.state_province, height=100, widgets={'state_province': pn.widgets.MultiChoice}),
                             pn.Param(app.param.covid19_date, widgets={'covid19_date': pn.widgets.DatePicker}),
                             pn.Param(app.param.confirmed_deaths),
                             pn.Param(app.param.ylog)
                            ),
                            app.plotAltairLineChart,
                            height=500
                  )

panel_app.show(host='localhost', port=8889, websocket_origin='localhost:8889', open=False)