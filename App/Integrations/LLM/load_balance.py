# Classe responsável pelo balanceamento de carga entre IA
import random
import time
from typing import Dict, List, Any
from datetime import datetime, timedelta

class LoadBalance:
    def __init__(self, llm_instances: List[Dict[str, Any]]):
        self.llm_instances = llm_instances
        self.instance_metrics = {
            instance["name"]: {
                "total_requests": 0,
                "successful_requests": 0,
                "failed_requests": 0,
                "average_response_time": 0,
                "last_request_time": None,
                "error_rate": 0,
                "health_score": 100,  # 0-100 health score
                "concurrent_requests": 0,
                "max_concurrent_requests": 10,  # Default max concurrent requests
                "request_history": []  # Last 100 requests for rolling metrics
            }
            for instance in llm_instances
        }
        self.proportion = self._calculate_initial_proportions()
        self.health_check_interval = 60  # seconds
        self.last_health_check = datetime.now()

    def _calculate_initial_proportions(self) -> Dict[str, int]:
        """Calculate initial proportions based on instance capabilities"""
        return {
            instance["name"]: 100 if len(self.llm_instances) == 1 else 50
            for instance in self.llm_instances
        }

    def update_metrics(self, instance_name: str, success: bool, response_time: float):
        """Update metrics for an instance after a request"""
        metrics = self.instance_metrics[instance_name]
        now = datetime.now()

        # Update basic metrics
        metrics["total_requests"] += 1
        if success:
            metrics["successful_requests"] += 1
        else:
            metrics["failed_requests"] += 1

        # Update response time (rolling average)
        if metrics["average_response_time"] == 0:
            metrics["average_response_time"] = response_time
        else:
            metrics["average_response_time"] = (metrics["average_response_time"] * 0.9 + response_time * 0.1)

        # Update request history
        metrics["request_history"].append({
            "timestamp": now,
            "success": success,
            "response_time": response_time
        })
        if len(metrics["request_history"]) > 100:
            metrics["request_history"].pop(0)

        # Update error rate
        metrics["error_rate"] = metrics["failed_requests"] / metrics["total_requests"] if metrics["total_requests"] > 0 else 0

        # Update health score
        self._update_health_score(instance_name)

        # Check if we need to recalculate proportions
        if (now - self.last_health_check).total_seconds() >= self.health_check_interval:
            self._recalculate_proportions()
            self.last_health_check = now

    def _update_health_score(self, instance_name: str):
        """Calculate health score based on various metrics"""
        metrics = self.instance_metrics[instance_name]
        
        # Calculate health components
        error_rate_score = max(0, 100 - (metrics["error_rate"] * 100))
        response_time_score = max(0, 100 - (metrics["average_response_time"] / 2))  # Assuming 2s is max acceptable
        
        # Combine scores with weights
        metrics["health_score"] = (
            error_rate_score * 0.6 +  # Error rate is most important
            response_time_score * 0.4
        )

    def _recalculate_proportions(self):
        """Recalculate instance proportions based on health scores"""
        total_health = sum(metrics["health_score"] for metrics in self.instance_metrics.values())
        
        if total_health > 0:
            self.proportion = {
                instance_name: int((metrics["health_score"] / total_health) * 100)
                for instance_name, metrics in self.instance_metrics.items()
            }
        else:
            # Fallback to equal distribution if all instances are unhealthy
            self.proportion = {
                instance_name: 100 // len(self.llm_instances)
                for instance_name in self.instance_metrics.keys()
            }

    def get_instance_for_method(self) -> Dict[str, Any]:
        """Get the best instance for the next request"""
        now = datetime.now()
        
        # Filter out instances that are at capacity
        available_instances = [
            instance for instance in self.llm_instances
            if self.instance_metrics[instance["name"]]["concurrent_requests"] < 
               self.instance_metrics[instance["name"]]["max_concurrent_requests"]
        ]

        if not available_instances:
            raise Exception("No available LLM instances")

        # Select instance based on proportions and health
        total_weight = sum(self.proportion[instance["name"]] for instance in available_instances)
        random_value = random.uniform(0, total_weight)
        
        current_sum = 0
        for instance in available_instances:
            current_sum += self.proportion[instance["name"]]
            if random_value <= current_sum:
                # Update concurrent requests
                self.instance_metrics[instance["name"]]["concurrent_requests"] += 1
                return instance

        # Fallback to random selection if something goes wrong
        return random.choice(available_instances)

    def release_instance(self, instance_name: str):
        """Release an instance after request completion"""
        if instance_name in self.instance_metrics:
            self.instance_metrics[instance_name]["concurrent_requests"] = max(
                0,
                self.instance_metrics[instance_name]["concurrent_requests"] - 1
            )

    def get_instance_metrics(self) -> Dict[str, Dict[str, Any]]:
        """Get current metrics for all instances"""
        return self.instance_metrics