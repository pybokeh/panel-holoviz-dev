# panel app examples

To run panel apps using Red Hat's OpenShift containerization platform, in the DeploymentConfig YAML, define the command to be:
panel serve your_app.py --address 0.0.0.0 --allow-websocket-origin=[your_openshift_cluster_route.com]

### covid19 example
![](images/covid19_panel_app.gif)
