"""
API Serializers for model data validation and response formatting.

Provides:
- SubscriptionPlanSerializer: Serialize/deserialize SubscriptionPlan model
- Input validation for JSON fields
- Custom validation methods
"""

import json
from saas.models.subscription import SubscriptionPlan


class SubscriptionPlanSerializer:
    """
    Serializer for SubscriptionPlan model.
    
    Handles:
    - Conversion of SubscriptionPlan objects to JSON-serializable dicts
    - Validation of input data before saving
    - JSON field parsing and validation
    """
    @staticmethod
    def serialize(plan):
        """
        Convert a SubscriptionPlan instance to a dictionary.
        Args:
            plan (SubscriptionPlan): Model instance
        Returns:
            dict: Serialized plan data
        """
        return {
            'id': plan.id,
            'name': plan.name,
            'price': float(plan.price),
            'duration_days': plan.duration_days,
            'features': plan.features,
            'created_at': plan.created_at.isoformat() if plan.created_at else None,
            'updated_at': plan.updated_at.isoformat() if plan.updated_at else None,
        }

    @staticmethod
    def serialize_list(plans):
        """
        Convert a queryset or list of SubscriptionPlan objects to list of dicts.
        """
        return [SubscriptionPlanSerializer.serialize(plan) for plan in plans]

    @staticmethod
    def validate_data(data):
        """
        Validate input data for SubscriptionPlan creation/update.
        Returns (is_valid, errors, cleaned_data)
        """
        errors = {}
        cleaned = {}
        # Name
        if 'name' not in data or not data['name']:
            errors['name'] = 'Name is required.'
        elif data['name'] not in dict(SubscriptionPlan.PLAN_CHOICES):
            errors['name'] = f"Plan name must be one of: {', '.join([c[0] for c in SubscriptionPlan.PLAN_CHOICES])}"
        else:
            cleaned['name'] = data['name']
        # Price
        try:
            price = float(data.get('price', 0))
            if price <= 0:
                errors['price'] = 'Price must be greater than 0.'
            else:
                cleaned['price'] = price
        except Exception:
            errors['price'] = 'Invalid price.'
        # Duration
        try:
            duration = int(data.get('duration_days', 0))
            if duration not in [30, 90, 365]:
                errors['duration_days'] = 'Duration must be 30, 90, or 365.'
            else:
                cleaned['duration_days'] = duration
        except Exception:
            errors['duration_days'] = 'Invalid duration.'
        # Features
        features = data.get('features')
        if isinstance(features, str):
            try:
                features = json.loads(features)
            except Exception:
                errors['features'] = 'Features must be a valid JSON array.'
        if not errors and (not isinstance(features, list)):
            errors['features'] = 'Features must be a list.'
        else:
            cleaned['features'] = features
        return (len(errors) == 0, errors, cleaned)

    @staticmethod
    def create_from_data(data):
        """
        Create a SubscriptionPlan from validated data dict.
        """
        plan = SubscriptionPlan(
            name=data['name'],
            price=data['price'],
            duration_days=data['duration_days'],
            features=data['features'],
        )
        plan.save()
        return plan

    @staticmethod
    def update_from_data(plan, data):
        """
        Update an existing SubscriptionPlan from validated data dict.
        """
        plan.name = data['name']
        plan.price = data['price']
        plan.duration_days = data['duration_days']
        plan.features = data['features']

