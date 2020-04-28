import pycovid19usAltair
import pycovid19globalAltair
import panel as pn

us_app = pycovid19usAltair.us_app
global_app = pycovid19globalAltair.global_app

#us_app.show(host='localhost', port=8889, websocket_origin='localhost:8889', open=False)

pn.serve({'By_Country': global_app, 'US_Only': us_app}, port=8890, websocket_origin='localhost:8890', show=False)
