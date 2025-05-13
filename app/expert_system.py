from . import db
from .models import Rule, RuleSymptom, Damage

class ForwardChainingEngine:
    def __init__(self):
        pass
        
    def diagnose(self, symptom_ids):
        """
        Implements the forward chaining algorithm to diagnose motor damage
        based on observed symptoms.
        
        Args:
            symptom_ids (list): List of symptom IDs observed
            
        Returns:
            dict: Diagnosed damage with causes and solutions
        """
        rules = Rule.query.all()
        potential_damages = []
        
        for rule in rules:
            rule_symptom_ids = [rs.symptom_id for rs in RuleSymptom.query.filter_by(rule_id=rule.id).all()]
            
            if all(symptom_id in symptom_ids for symptom_id in rule_symptom_ids):
                damage = Damage.query.get(rule.damage_id)
                potential_damages.append(damage)
                
        if potential_damages:
            damage = potential_damages[0]  # Simplification: pick first match
            return damage.to_dict()
        else:
            return None