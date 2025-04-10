from .LLM.index import LLM
from .Datasources.index import Datasource
from dotenv import load_dotenv,find_dotenv
import os,json,time
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
                                metrics = self.LLMLoadBalance.get_instance_metrics()
                                instance_metrics = metrics.get(instance_name, {})
                                concurrent_requests = instance_metrics.get("concurrent_requests", 0)
                                max_concurrent = instance_metrics.get("max_concurrent_requests", 10)

                                if concurrent_requests >= max_concurrent:
                                    print(f"Instance {instance_name} reached maximum concurrent requests. Trying to balance load.")
                                    
                                    # Try to find an available instance
                                    selected_instance = self.LLMLoadBalance.get_instance_for_method()
                                    if selected_instance:
                                        print(f"Selected alternative instance: {selected_instance['name']}")
                                        instance_name = selected_instance['name']
                                        instance = selected_instance
                                    else:
                                        print("No available instances.")
                                        return None
                            
                            obj = instance['instance']
                            
                            if hasattr(obj, method_name):
                                start_time = time.time()
                                try:
                                    method = getattr(obj, method_name)
                                    result = method(*args, **kwargs)
                                    response_time = time.time() - start_time
                                    
                                    if key == "llm":
                                        self.LLMLoadBalance.update_metrics(
                                            instance_name,
                                            success=True,
                                            response_time=response_time
                                        )
                                        print("Load balancing proportions:", self.LLMLoadBalance.proportion)
                                    
                                    return result
                                except Exception as e:
                                    if key == "llm":
                                        response_time = time.time() - start_time
                                        self.LLMLoadBalance.update_metrics(
                                            instance_name,
                                            success=False,
                                            response_time=response_time
                                        )
                                    raise e
                                finally:
                                    if key == "llm":
                                        self.LLMLoadBalance.release_instance(instance_name)
                            else:
                                return None
                        else:
                            return None

        return None