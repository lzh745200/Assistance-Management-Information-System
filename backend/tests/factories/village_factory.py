"""SupportedVillage and related model factories."""

from datetime import datetime, timezone

from app.models.supported_village import (
    SupportedVillage, VillagePopulation, VillageIncome,
    ForceInvestment, IndustrySupport, InfrastructureImprovement,
    PartyBuildingSupport, MedicalSupport, ConsumptionSupport,
    EmploymentSupport, EducationSupport, SupportFunding,
)


class SupportedVillageFactory:
    @staticmethod
    def build(**kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            village_name="测试村",
            province="贵州省",
            city="贵阳市",
            county="测试县",
            township="测试镇",
            latitude=26.65,
            longitude=106.63,
            is_three_regions=False,
            is_border_area=False,
            is_ethnic_area=True,
            is_revolutionary_area=False,
            is_key_county=False,
            transition_status="none",
            created_at=now,
            updated_at=now,
        )
        data.update(kwargs)
        return SupportedVillage(**data)

    @staticmethod
    def create(db, **kwargs):
        obj = SupportedVillageFactory.build(**kwargs)
        db.add(obj)
        db.flush()
        return obj

    @staticmethod
    def build_with_full_info(**kwargs):
        """Build a village with all boolean flags set for comprehensive testing."""
        kwargs.setdefault("is_three_regions", True)
        kwargs.setdefault("is_border_area", True)
        kwargs.setdefault("is_ethnic_area", True)
        kwargs.setdefault("is_revolutionary_area", True)
        kwargs.setdefault("is_key_county", True)
        kwargs.setdefault("is_provincial_demo", True)
        kwargs.setdefault("is_hundred_village_demo", True)
        kwargs.setdefault("is_tiered_development", True)
        kwargs.setdefault("is_cross_province", True)
        kwargs.setdefault("is_cross_city", True)
        kwargs.setdefault("is_cross_unit_cooperation", True)
        kwargs.setdefault("is_in_overall_plan", True)
        return SupportedVillageFactory.build(**kwargs)


class VillagePopulationFactory:
    @staticmethod
    def build(village_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            village_id=village_id,
            year=2024,
            total_households=500,
            total_population=2000,
            male_population=1050,
            female_population=950,
            ethnic_population=800,
            labor_force=1200,
            migrant_workers=300,
            poor_households=50,
            poor_population=180,
            created_at=now,
            updated_at=now,
        )
        data.update(kwargs)
        return VillagePopulation(**data)

    @staticmethod
    def create(db, village_id=1, **kwargs):
        obj = VillagePopulationFactory.build(village_id=village_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj


class VillageIncomeFactory:
    @staticmethod
    def build(village_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            village_id=village_id,
            year=2024,
            total_income=5000000.00,
            collective_income=200000.00,
            per_capita_income=12500.00,
            farming_income=2000000.00,
            business_income=1500000.00,
            wage_income=1000000.00,
            property_income=300000.00,
            transfer_income=200000.00,
            created_at=now,
            updated_at=now,
        )
        data.update(kwargs)
        return VillageIncome(**data)

    @staticmethod
    def create(db, village_id=1, **kwargs):
        obj = VillageIncomeFactory.build(village_id=village_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj


class SupportFundingFactory:
    @staticmethod
    def build(village_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(
            village_id=village_id,
            year=2024,
            military_fund=1000000.00,
            local_fund=500000.00,
            other_fund=100000.00,
            created_at=now,
            updated_at=now,
        )
        data.update(kwargs)
        return SupportFunding(**data)

    @staticmethod
    def create(db, village_id=1, **kwargs):
        obj = SupportFundingFactory.build(village_id=village_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj


# Industry, Infrastructure, PartyBuilding, etc. factory classes
class ForceInvestmentFactory:
    @staticmethod
    def build(village_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(village_id=village_id, year=2024, force_count=10,
                     investment_amount=500000.00, created_at=now, updated_at=now)
        data.update(kwargs)
        return ForceInvestment(**data)

    @staticmethod
    def create(db, village_id=1, **kwargs):
        obj = ForceInvestmentFactory.build(village_id=village_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj


class IndustrySupportFactory:
    @staticmethod
    def build(village_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(village_id=village_id, year=2024, industry_count=3,
                     total_investment=800000.00, created_at=now, updated_at=now)
        data.update(kwargs)
        return IndustrySupport(**data)

    @staticmethod
    def create(db, village_id=1, **kwargs):
        obj = IndustrySupportFactory.build(village_id=village_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj


class InfrastructureImprovementFactory:
    @staticmethod
    def build(village_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(village_id=village_id, year=2024, project_count=5,
                     total_investment=2000000.00, created_at=now, updated_at=now)
        data.update(kwargs)
        return InfrastructureImprovement(**data)

    @staticmethod
    def create(db, village_id=1, **kwargs):
        obj = InfrastructureImprovementFactory.build(village_id=village_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj


class PartyBuildingSupportFactory:
    @staticmethod
    def build(village_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(village_id=village_id, year=2024, activity_count=12,
                     participant_count=300, created_at=now, updated_at=now)
        data.update(kwargs)
        return PartyBuildingSupport(**data)

    @staticmethod
    def create(db, village_id=1, **kwargs):
        obj = PartyBuildingSupportFactory.build(village_id=village_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj


class MedicalSupportFactory:
    @staticmethod
    def build(village_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(village_id=village_id, year=2024, clinic_count=1,
                     doctor_count=3, patient_count=500, created_at=now, updated_at=now)
        data.update(kwargs)
        return MedicalSupport(**data)

    @staticmethod
    def create(db, village_id=1, **kwargs):
        obj = MedicalSupportFactory.build(village_id=village_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj


class ConsumptionSupportFactory:
    @staticmethod
    def build(village_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(village_id=village_id, year=2024, consumption_amount=300000.00,
                     participant_count=200, created_at=now, updated_at=now)
        data.update(kwargs)
        return ConsumptionSupport(**data)

    @staticmethod
    def create(db, village_id=1, **kwargs):
        obj = ConsumptionSupportFactory.build(village_id=village_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj


class EmploymentSupportFactory:
    @staticmethod
    def build(village_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(village_id=village_id, year=2024, trained_count=150,
                     employed_count=80, created_at=now, updated_at=now)
        data.update(kwargs)
        return EmploymentSupport(**data)

    @staticmethod
    def create(db, village_id=1, **kwargs):
        obj = EmploymentSupportFactory.build(village_id=village_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj


class EducationSupportFactory:
    @staticmethod
    def build(village_id=1, **kwargs):
        now = datetime.now(timezone.utc)
        data = dict(village_id=village_id, year=2024, school_count=2,
                     student_count=300, scholarship_count=20, created_at=now, updated_at=now)
        data.update(kwargs)
        return EducationSupport(**data)

    @staticmethod
    def create(db, village_id=1, **kwargs):
        obj = EducationSupportFactory.build(village_id=village_id, **kwargs)
        db.add(obj)
        db.flush()
        return obj
