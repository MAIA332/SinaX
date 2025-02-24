from .LLM.index import LLM
from .Datasources.index import Datasource
from dotenv import load_dotenv,find_dotenv
import os,json
from .LLM.load_balance import LoadBalance

class Source:
    def __init__(self):
        load_dotenv(find_dotenv()) 
        self.services = self.load_services()
        
        llm = LLM(self.services["LLM"])
        dt = Datasource(self.services["VECTORS_DATABASE"])

        self.sources = [
            {
                "llm":llm.LLMs_isntances,
                "dt":dt.datasource_isntances
            }
        ]

        self.LLMLoadBalance = LoadBalance(self.sources[0]["llm"])

    def load_services(self):

        services_path = os.getenv("SERVICES")

        with open(services_path,"r") as file:
            services = json.load(file)
            return services
        
    def execute_method_on_instance(self, name, method_name, *args, **kwargs):
        executed_instances = set()

        for source in self.sources:
            for key, instances in source.items():

                for instance in instances:
                    instance_name = instance['name']

                    if instance_name == name:
                        if instance_name not in executed_instances:
                            executed_instances.add(instance_name)

                            if key == "llm":
                                print(self.LLMLoadBalance.instance_load.get(instance_name, 0))
                                if self.LLMLoadBalance.instance_load.get(instance_name, 0) >= self.LLMLoadBalance.get_max_load_for_instance(instance_name):
                                    print(f"Instância {instance_name} atingiu a carga máxima proporcional. Tentando balancear carga.")
                                    
                                    # Tenta encontrar uma instância com carga disponível
                                    selected_instance = self.LLMLoadBalance.get_instance_for_method()
                                    if selected_instance:
                                        print(f"Selecionando outra instância para execução: {selected_instance['name']}")
                                        instance_name = selected_instance['name']
                                    else:
                                        print("Nenhuma instância disponível para execução.")
                                        return None
                            
                            obj = instance['instance']
                            
                            if hasattr(obj, method_name):
                                method = getattr(obj, method_name)
                                result = method(*args, **kwargs)

                                if key == "llm":
                                    print("balanceamento de carga...",self.LLMLoadBalance.proportion)

                                    self.LLMLoadBalance.update_load(instance_name)

                                return result
                            else:
                                return None
                        else:
                            return None

        return None