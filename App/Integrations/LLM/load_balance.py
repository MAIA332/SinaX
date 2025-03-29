# Classe responsável pelo balanceamento de carga entre IA
import random

class LoadBalance:
    def __init__(self,llm_instances):
        self.llm_instances = llm_instances
        self.proportion = {i["name"]:120 if len(self.llm_instances)==1 else 0 for i in self.llm_instances}
        self.instance_load = {i["name"]: 0 for i in self.llm_instances}  # Track the load on each instance

    def set_proportion(self,proportion):
        self.proportion = proportion

    def get_max_load_for_instance(self, instance_name):
        """Calcula a carga máxima para uma instância baseada na proporção"""
        # A carga máxima é determinada pela proporção individual, não pela soma de todas as proporções
        instance_proportion = self.proportion.get(instance_name, 0)
        
        # Agora, a carga máxima será definida pela proporção de cada instância, sem depender da soma total
        return instance_proportion  # Considera a proporção diretamente

    def get_instance_for_method(self):
        """Retorna uma instância disponível com base na proporção e carga atual"""
        available_instances = [
            instance for instance in self.llm_instances
            if self.instance_load.get(instance["name"], 0) < self.get_max_load_for_instance(instance["name"])
        ]
        
        if not available_instances:
            print("Todas as instâncias indisponíveis... resetando")
            proportion = {i["name"]:3 if len(self.llm_instances)==1 else 0 for i in self.llm_instances}
            self.set_proportion(proportion)
            return None
        
        # Retorna a instância com a menor carga atual
        return min(available_instances, key=lambda x: self.instance_load.get(x["name"], 0))

    def update_load(self, instance_name):
        """
        Update the load for an instance when it has been selected to handle a request.
        :param instance_name: The name of the LLM instance.
        """
        if instance_name in self.instance_load:
            self.instance_load[instance_name] += 1