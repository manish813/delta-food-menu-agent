"""SSR (Special Service Request) code definitions for airline meal types"""

SSR_CODE_DESCRIPTIONS = {
    # Pre-Select Meals
    "PYML": "Reserved for Pre-Select exceptions / one-off scenario",
    "PZML": "Reserved for Pre-Select exceptions / one-off scenarios",
    "JVML": "Jain Asian vegetarian style meal contains not root vegetables",
    "PBML": "Pre-Select a standard complimentary beef entree meal",
    "PCML": "Pre-Select a standard complimentary chicken entree meal",
    "PDML": "Pre-Select lunch: Sandwich muffaletta, burrito, BLT or similar",
    "PEML": "Pre-Select Breakfast/brunch: omelette, frittata, strata or similar",
    "PFML": "Pre-Select a standard complimentary seafood entree meal",
    "PGML": "Pre-Select breakfast/brunch: grain option such as oatmeal, granola, or similar",
    "PLML": "Pre-Select lunch; entree salad",
    "PNML": "Pre-Select breakfast/brunch: non egg breakfast item: pancakes, waffles, french toast or similar",
    "POML": "Pre-Select lunch: cold plate continental meat and cheese",
    "PPML": "Pre-Select pasta entree meal (appetizer may contain meat)",
    "PVML": "Pre-Select Vegetarian meal(not pasta)",
    "PWML": "Pre-Select a standard complimentary White Meat meal",
    "PXML": "Reserved for Pre-Select Exceptions",
    
    # Special Dietary Meals
    "AVML": "Asian vegetarian meal",
    "BBML": "Baby meal(May be ordered for any child under two (2) not eating solid food)",
    "BLML": "Bland meal",
    "CHML": "Child meal(May be ordered for a ticketed passenger of any age)",
    "CNML": "Chinese meal(available in addition to the option to pre-select a standard complimentary meal)",
    "DBML": "Diabetic meal",
    "GFML": "Gluten-Free meal",
    "HNML": "Hindu meal(contains vegetarian food components similar to the Asian vegetarian meal)",
    "JPML": "Japanese meal(available in addition to the option to pre-select a standard complimentary meal)",
    "KRML": "Korean meal(available in addition to the option to pre-select a standard complimentary meal)",
    "KSML": "Kosher(Kosher meals are replaced with Passover meals during Passover)",
    "LFML": "Calorie/Cholesterol/Fat free meal",
    "LSML": "Low Sodium meal",
    "MOML": "Moslem(MOML not available on flights departing from ROR)",
    "RCML": "Resort Couple/Honeymoon Couple Meal",
    "TDML": "Toddler meal(May be ordered for any child under two (2) eating solid food)",
    "VGML": "Vegan",
    "VLML": "Vegetarian",
    "SPML": "Special Meal",
    "SFML": "Sea Food Meal",
    "FPML": "Fruit Plate Meal/New Industry SSR-EFF",
    "HFML": "High Fiber Meal",
    "LCML": "Low Calorie",
    "LPML": "Low Protein Meal",
    "NLML": "Non Lactose Meal",
    "ORML": "Oriental Meal",
    "PRML": "Low Purin Meal",
    "PSML": "To Insure Proper Meal Catering",
    "RVML": "Raw Vegetarian Meal",
    "PMML": "Premium Meal Service Option(Offered by Third Party Vendor)",
    "NSML": "No Salt",
    "VJML": "Vegetarian Jain Meal(Offered on Flights Operated by KE Out of ICN)",
    "VOML": "Vegetarian Oriental Meal(Offered on Flights Operated by KE Out of ICN)",
    "LDML": "Liquid Diet Meal(Offered on Flights Operated by KE Out of ICN)",
    "NOML": "NO Meal",
    "ICML": "Infant Child Meal(For KOREAN Air Flights Only)"
}

def get_ssr_description(ssr_code: str) -> str:
    """Get description for SSR code"""
    return SSR_CODE_DESCRIPTIONS.get(ssr_code, f"Unknown SSR code: {ssr_code}")