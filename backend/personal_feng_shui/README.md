# Personal Feng Shui AI System

Complete classical Feng Shui analysis engine with AI-ready architecture.

## System Architecture

```
personal_feng_shui/
├── __init__.py              # Module exports
├── config.py                # Configuration & settings
├── analyzer.py              # Main analysis engine
├── knowledge_base.py        # Classical Feng Shui knowledge
├── bazi_calculator.py       # Four Pillars (Ba Zi) calculations
├── element_engine.py        # Five Elements relationships
└── remedy_database.py       # Remedies & recommendations
```

## Features Implemented

### 1. Classical Feng Shui Calculations
- **Kua Number**: Eight Mansions formula with gender variations
- **Ba Zi (Four Pillars)**: Year pillar, element analysis, life phase
- **Five Elements**: Complete productive/destructive cycle engine
- **Eight Directions**: Lucky/unlucky direction mapping with meanings
- **Bagua Map**: 9 life areas with element associations

### 2. Knowledge Base
- 5 Elements with attributes (colors, shapes, directions, qualities)
- 9 Bagua life areas (wealth, fame, love, family, etc.)
- Kua direction mappings for all 8 numbers
- Heavenly Stems & Earthly Branches (Chinese zodiac)
- Life goals to element mapping

### 3. Analysis Components
- **Personal Profile**: Kua, element, group classification
- **Ba Zi Analysis**: Day master, element strength, life phase
- **Direction Analysis**: Scores for all 8 directions with meanings
- **Element Balance**: Beneficial/avoid elements
- **Goal Alignment**: How well personal element supports life goals

### 4. Recommendations Engine
- Prioritized recommendations (high/medium/low)
- Direction optimization (desk, bed placement)
- Element strengthening strategies
- Goal-specific feng shui adjustments
- Budget-aware remedy suggestions

### 5. Remedies Database
- 20+ remedies per element (100+ total)
- Organized by: crystals, plants, colors, furniture, decor, lighting, water features
- Each remedy includes: description, placement, cost, difficulty, benefits, care
- Goal-specific remedy lists (career, wealth, relationships, health, recognition)
- Budget filtering (low/medium/high cost)

## API Endpoint

**POST** `/api/personal-feng-shui/analyze`

### Request Format

```json
{
  "profile": {
    "birthYear": 1990,
    "gender": "male",
    "birthMonth": 6,
    "birthDay": 15,
    "goals": ["career", "health", "relationships"],
    "preferredDirection": "N",
    "budget": "medium"
  }
}
```

**Required fields**: `birthYear`, `gender`  
**Optional fields**: `birthMonth`, `birthDay`, `goals`, `preferredDirection`, `budget`

### Response Structure

```json
{
  "success": true,
  "data": {
    "overall_score": 78,
    "analysis_level": "detailed",
    
    "personal_profile": {
      "birth_year": 1990,
      "age": 36,
      "gender": "male",
      "kua_number": 4,
      "kua_group": "east",
      "primary_element": "metal",
      "element_strength": "moderate",
      "life_phase": {
        "phase": "maturity",
        "description": "Achievement and consolidation"
      }
    },
    
    "bazi_analysis": {
      "year_pillar": {...},
      "day_master": {...},
      "element_needs": {
        "beneficial_elements": ["metal", "earth"],
        "avoid_elements": ["fire"]
      }
    },
    
    "directions": {
      "best_direction": "N",
      "health_direction": "S",
      "relationship_direction": "E",
      "worst_direction": "NE",
      "current_score": 88,
      "detailed_scores": {...}
    },
    
    "element_balance": {
      "primary_element": "metal",
      "beneficial_elements": ["metal", "earth"],
      "avoid_elements": ["fire"],
      "enhancements": {
        "colors": ["white", "gray", "silver"],
        "items": ["wind_chimes", "metal_sculptures", ...]
      }
    },
    
    "goal_analysis": {
      "goals": ["career", "health"],
      "goal_scores": {"career": 85, "health": 72},
      "goal_specific_remedies": {...}
    },
    
    "scores": {
      "overall": 78,
      "element_alignment": 70,
      "direction_alignment": 88,
      "goal_alignment": 78
    },
    
    "recommendations": [
      {
        "priority": "high",
        "category": "direction",
        "title": "Face N for Success",
        "description": "Orient your desk...",
        "implementation": "Use a compass..."
      },
      ...
    ],
    
    "remedies": {
      "element_remedies": [...],
      "budget_friendly": [...],
      "priority_actions": [...]
    },
    
    "bagua_guidance": {...}
  }
}
```

## Configuration

Edit `config.py` to customize:

```python
class PersonalFengShuiConfig:
    ENABLE_BAZI = True
    ENABLE_FLYING_STARS = False  # Future feature
    ENABLE_ADVANCED_REMEDIES = True
    
    SCORE_WEIGHTS = {
        'element_alignment': 0.35,
        'direction_alignment': 0.30,
        'life_goal_match': 0.20,
        'element_balance': 0.15
    }
    
    MAX_RECOMMENDATIONS = 12
```

## Testing

```bash
# Test import
cd backend
python3 -c "from personal_feng_shui import analyze_personal_feng_shui; print('OK')"

# Test analysis
python3 -c "
from personal_feng_shui import analyze_personal_feng_shui
result = analyze_personal_feng_shui({
    'birthYear': 1990,
    'gender': 'male',
    'goals': ['career', 'health']
})
print(f'Score: {result[\"overall_score\"]}')
print(f'Kua: {result[\"personal_profile\"][\"kua_number\"]}')
"

# Test API endpoint
curl -X POST http://localhost:3000/api/personal-feng-shui/analyze \
  -H "Content-Type: application/json" \
  -d '{
    "profile": {
      "birthYear": 1990,
      "gender": "male",
      "goals": ["career"]
    }
  }'
```

## Classical Formulas Implemented

### Kua Number Calculation
```
Pre-2000:
  Male: (10 - (year % 100 reduced)) % 9
  Female: (5 + (year % 100 reduced)) % 9

Post-2000:
  Male: (9 - (year % 100 reduced)) % 9
  Female: (6 + (year % 100 reduced)) % 9

Replace 5 with: 2 (female) or 8 (male)
```

### Five Elements Cycles
- **Productive**: Water→Wood→Fire→Earth→Metal→Water
- **Destructive**: Water→Fire, Fire→Metal, Metal→Wood, Wood→Earth, Earth→Water

### Eight Directions Hierarchy
1. **Sheng Qi** (Generating Breath): Success & prosperity
2. **Tian Yi** (Heavenly Doctor): Health & healing
3. **Nian Yan** (Longevity): Relationships & romance
4. **Fu Wei** (Personal Growth): Stability
5. **Huo Hai** (Accidents): Minor mishaps
6. **Wu Gui** (Five Ghosts): Conflicts
7. **Liu Sha** (Six Killings): Health issues
8. **Jue Ming** (Total Loss): Worst direction

## Integration Notes

- **Self-contained**: All logic within `personal_feng_shui/` folder
- **No conflicts**: Independent from outdoor/indoor analysis systems
- **Modular**: Each component can be enhanced independently
- **Extensible**: Add Flying Stars, advanced Ba Zi, or ML recommendations later
- **Classical accuracy**: Implements authentic formulas from Eight Mansions school

## Future Enhancements

1. **Flying Stars** (Xuan Kong): Time-space analysis
2. **Full Ba Zi**: Month, day, hour pillars + 10-year luck cycles
3. **ML Recommendations**: Learn from user feedback
4. **Compatibility Analysis**: Person-to-person, person-to-space
5. **Timing Analysis**: Auspicious dates for activities
6. **3D Visualization**: Interactive Bagua overlays
7. **Community Features**: Share success stories

## Notes

- All calculations follow classical Feng Shui formulas
- Sistema modular no interfiere con análisis exterior/interior existente
- Configuración centralizada en `config.py`
- Base de conocimientos completa en `knowledge_base.py`
- Recomendaciones priorizadas y personalizadas
- Compatible con expansión futura (ML, Flying Stars, etc.)
