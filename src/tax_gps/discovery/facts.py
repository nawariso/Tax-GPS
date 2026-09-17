"""Collection of explicit profile facts for opportunity decisions."""

from dataclasses import dataclass

from tax_gps.discovery.eligibility import EligibilityFact
from tax_gps.opportunity import opportunity_ids
from tax_gps.opportunity.models import OpportunityDefinition
from tax_gps.profile.models import UserProfile


@dataclass(frozen=True, slots=True)
class CollectedOpportunityFacts:
    intent: EligibilityFact
    conditions: tuple[EligibilityFact, ...]


def collect_facts(
    definition: OpportunityDefinition, profile: UserProfile
) -> CollectedOpportunityFacts:
    prefix = definition.opportunity_id
    if definition.opportunity_id == opportunity_ids.ARTWORK:
        artwork = profile.opportunity_facts.artwork
        return CollectedOpportunityFacts(
            EligibilityFact(f"{prefix}.intrinsic_intent", artwork.intends_to_purchase),
            (
                EligibilityFact("artwork.qualifying", artwork.artwork_is_qualifying),
                EligibilityFact("artwork.seller", artwork.seller_is_qualifying),
                EligibilityFact("artwork.has_required_document", artwork.has_required_document),
            ),
        )
    if definition.opportunity_id == opportunity_ids.SOLAR_ROOFTOP:
        solar = profile.opportunity_facts.solar_rooftop
        return CollectedOpportunityFacts(
            EligibilityFact(f"{prefix}.intrinsic_intent", solar.intends_to_install),
            (
                EligibilityFact("solar_rooftop.is_natural_person", solar.is_natural_person),
                EligibilityFact(
                    "solar_rooftop.single_system_single_use", solar.single_system_single_use
                ),
                EligibilityFact(
                    "solar_rooftop.building_is_occupiable", solar.building_is_occupiable
                ),
                EligibilityFact(
                    "solar_rooftop.on_grid_connected_to_mea_or_pea",
                    solar.on_grid_connected_to_mea_or_pea,
                ),
                EligibilityFact(
                    "solar_rooftop.paid_to_vat_registrant", solar.paid_to_vat_registrant
                ),
                EligibilityFact(
                    "solar_rooftop.has_electronic_tax_invoice",
                    solar.has_electronic_tax_invoice,
                ),
                EligibilityFact(
                    "solar_rooftop.grid_connection_completed_in_tax_year",
                    solar.grid_connection_completed_in_tax_year,
                ),
                EligibilityFact(
                    "solar_rooftop.no_duplicate_tax_benefit", solar.no_duplicate_tax_benefit
                ),
                EligibilityFact(
                    "solar_rooftop.meets_director_general_conditions",
                    solar.meets_director_general_conditions,
                ),
            ),
        )
    return CollectedOpportunityFacts(EligibilityFact(f"{prefix}.intrinsic_intent", None), ())
