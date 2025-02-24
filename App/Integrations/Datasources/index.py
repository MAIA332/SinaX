import os,json

class Datasource:
    def __init__(self,services):
        
        self.services = services
        self.datasource = self.determine_datasource()
        self.datasource_isntances = self.instance_datasource()

    def instance_datasource(self):
        instances = []
        for i in self.datasource:
            plugin_name = i["plugin_name"]
            
            lib = __import__(f"Integrations.Datasources.{plugin_name}.implementation", fromlist=[""])
            class_name = i["entry_point"]

            plugin_class = getattr(lib, class_name)
        
            object_instance = plugin_class()

            instances.append({
                "name":plugin_name,
                "instance":object_instance
            })

        return instances
        
    def determine_datasource(self):
        datasource = [self.services[i] for i in self.services if self.services[i]["habilited"] == True]
        return datasource