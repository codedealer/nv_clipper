# Adding New Settings to the GUI Application

This guide walks through the complete process of adding a new setting to the yt_clipper GUI application. The process involves multiple files and steps to ensure proper integration between CLI and GUI modes.

## Overview

The yt_clipper GUI application uses a unified settings system where settings are defined once and automatically available for both CLI and GUI usage. The system involves:

1. **Schema Definition** - Settings are defined in a central schema
2. **Python Backend** - Settings are implemented in Python dataclasses and processing logic
3. **TypeScript Frontend** - Settings are typed and made available to the Vue.js interface
4. **GUI Interface** - Settings are added to the actual user interface components
5. **Processing Integration** - Settings flow through the processing pipeline

## Step-by-Step Process

### Step 1: Add Setting to Schema (argparser.py)

File: `src/clipper/argparser.py`

Add the setting definition to the `getSettingsSchema()` function in the appropriate section (general, video, etc.):

```python
"your_setting": {
    "type": "integer",  # or "string", "boolean", "number", "string_list"
    "description": "Description of what this setting does",
    "min": 0,  # For numeric types (optional)
    "max": 100,  # For numeric types (optional)
    "default": None,  # Default value, use None for auto-calculated
    "cli_args": ["--your-setting", "-ys"],  # CLI argument names
},
```

Add the setting to the appropriate argument group mapping:

```python
# In the group_mapping dictionary
'your_setting': output_options,  # or appropriate group
```

**Setting Types:**
- `"boolean"` - True/False values
- `"integer"` - Whole numbers (int)
- `"number"` - Decimal numbers (float)
- `"string"` - Text values
- `"string_list"` - Array of strings

### Step 2: Add to GUI Settings Dataclass (settings_manager.py)

File: `src/clipper/gui/settings_manager.py`

Add the field to the `GeneralSettings` dataclass in the appropriate section:

```python
@dataclass
class GeneralSettings:
    # ... existing fields ...
    your_setting: Optional[int] = None  # Use appropriate type
```

**Type Mapping:**
- Schema `"boolean"` → Python `bool`
- Schema `"integer"` → Python `int` or `Optional[int]`
- Schema `"number"` → Python `float` or `Optional[float]`
- Schema `"string"` → Python `str`
- Schema `"string_list"` → Python `List[str]`

Use `Optional[]` for settings that can be None (auto-calculated or optional).

### Step 3: Add to Processing Pipeline (engine.py)

File: `src/clipper/gui/engine.py`

Add the setting to the `safe_gui_settings` mapping in the `_apply_gui_settings_to_clipper_state` method:

```python
safe_gui_settings = {
    # ... existing mappings ...
    'your_setting': 'yourSetting',  # GUI key -> Clipper state key
}
```

**Key Naming Convention:**
- GUI settings use `snake_case` (matches Python dataclass fields)
- Clipper state uses `camelCase` (matches CLI argument parsing)

### Step 4: Add to TypeScript Interface (settings.ts)

File: `src/gui-frontend/src/types/settings.ts`

Add the field to the `GeneralSettings` interface:

```typescript
export interface GeneralSettings {
  // ... existing fields ...
  your_setting?: number  // Use appropriate TypeScript type
}
```

**Type Mapping:**
- Python `bool` → TypeScript `boolean`
- Python `int/Optional[int]` → TypeScript `number/number?`
- Python `float/Optional[float]` → TypeScript `number/number?`
- Python `str` → TypeScript `string`
- Python `List[str]` → TypeScript `string[]`

Use optional (`?`) for settings that can be undefined.

### Step 5: Add to Settings Categories (Optional)

In the same `settings.ts` file, add your setting to an appropriate category in `SETTINGS_CATEGORIES`:

```typescript
{
  id: 'quality',
  name: 'Quality & Encoding',
  settings: ['crf', 'target_max_bitrate', 'your_setting']  // Add here
}
```

### Step 6: Add to GUI Settings Panel (SettingsPanel.vue)

File: `src/gui-frontend/src/components/SettingsPanel.vue`

Add the actual UI component for the setting in the appropriate tab. Choose the tab that best matches your setting's category:

**For boolean settings:**
```vue
<el-form-item label="Your Setting Name">
  <el-switch
    :model-value="props.settings?.your_setting || false"
    @update:model-value="(value) => updateBooleanSetting('your_setting', value)"
    :loading="isLoading"
  />
  <el-text class="setting-help" type="info">Description of what this setting does</el-text>
</el-form-item>
```

**For numeric settings:**
```vue
<el-form-item label="Your Setting (0-100)">
  <el-input-number
    :model-value="props.settings?.your_setting || null"
    @change="(value) => handleNumberChange('your_setting', value)"
    :min="0"
    :max="100"
    :disabled="isLoading"
    style="width: 150px"
    placeholder="Auto"
  />
  <el-text class="setting-help" type="info">Description and valid range information</el-text>
</el-form-item>
```

**For text settings:**
```vue
<el-form-item label="Your Setting">
  <el-input
    :model-value="getCurrentTextValue('your_setting')"
    @input="(value) => handleTextInput('your_setting', value)"
    @blur="() => handleTextBlur('your_setting')"
    @keyup.enter="() => handleTextEnter('your_setting')"
    :disabled="isLoading"
    placeholder="Enter value here"
  />
  <el-text class="setting-help" type="info">Description of what this setting does</el-text>
</el-form-item>
```

**Available Tabs:**
- `"logging"` - Log levels and debugging options
- `"input"` - Video input and download settings
- `"output"` - Video output, quality, and encoding settings
- `"ai_gpu"` - AI interpolation and GPU settings
- `"other"` - General options like preview mode
- `"ytdl"` - YouTube downloader configuration
- `"cache"` - Video caching settings

## Example: Adding CRF Setting

Here's the complete example of adding the CRF (Constant Rate Factor) setting:

### 1. argparser.py
```python
"crf": {
    "type": "integer",
    "description": "Set constant rate factor (crf). Default is 30 for video file input. Automatically set to a factor of the detected video bitrate",
    "min": 0,
    "max": 51,
    "default": None,
    "cli_args": ["--crf"],
},
```

### 2. settings_manager.py
```python
crf: Optional[int] = None  # Constant rate factor (0-51), default is auto-calculated
```

### 3. engine.py
```python
'crf': 'crf',
```

### 5. SettingsPanel.vue
```vue
<el-form-item label="CRF (0-51)">
  <el-input-number
    :model-value="props.settings?.crf || null"
    @change="(value) => handleNumberChange('crf', value)"
    :min="0"
    :max="51"
    :disabled="isLoading"
    style="width: 150px"
    placeholder="Auto"
  />
  <el-text class="setting-help" type="info">Constant Rate Factor for quality control. Lower = higher quality, larger files. Default is 30 for video input.</el-text>
</el-form-item>
```

## Important Notes

### Settings Flow
Settings flow through the system in this order:
1. **GUI Settings** (user input) →
2. **Clipper State** (via engine mapping) →
3. **Processing Pipeline** (actual video processing)

### Default Values
- Use `None`/`undefined` for auto-calculated settings
- Use explicit defaults for settings with fixed fallback values
- Document auto-calculation behavior in comments

### Validation
- Numeric ranges are enforced by the schema (`min`/`max`)
- CLI validation happens in `getArgs()` function
- GUI validation should be added to frontend components

### Testing
After adding a setting:
1. Test CLI usage: `python -m clipper.yt_clipper --your-setting 50 markup.json`
2. For GUI-only tuning parameters (no CLI args) like `lgg_projection_gain` (an intensity multiplier for Lift/Gamma/Gain color wheel hue projection), ensure:
   - Added to schema with empty `cli_args` list so it persists
   - Added to `GeneralSettings` dataclass (`lgg_projection_gain: float = 1.5`)
   - Consumed in frontend logic (e.g., passed into `buildLggFilterFromWheels`)
   - UI control updates backend via `update_general_settings` API

Example schema entry (general section):
```python
"lgg_projection_gain": {
  "type": "number",
  "description": "Intensity multiplier for Lift/Gamma/Gain color wheel hue projection (0.5-2.0)",
  "min": 0.5,
  "max": 2.0,
  "default": 1.5,
  "cli_args": [],
},
```

Frontend usage snippet:
```ts
const projectionGain = settingsStore.generalSettings?.lgg_projection_gain ?? 1.5
buildLggFilterFromWheels(wheelsInput, globalGamma, projectionGain)
```
2. Test GUI usage: Verify setting appears in Settings Panel and persists when saved
3. Test processing: Ensure setting affects video output as expected
4. Test validation: Verify min/max ranges work in both CLI and GUI
5. Check for conflicts: Ensure no duplicate argument definitions exist

### Avoiding Conflicts
**Important:** If your setting was previously defined manually in `getArgParser()`, you must remove the manual definition to avoid `ArgumentError: conflicting option string` errors. The schema-based system automatically handles argument creation.

## File Summary

| File | Purpose | Changes Required |
|------|---------|------------------|
| `argparser.py` | Schema definition, CLI parsing | Add to schema and group mapping |
| `settings_manager.py` | Python dataclass | Add field to GeneralSettings |
| `engine.py` | Processing integration | Add to safe_gui_settings mapping |
| `settings.ts` | TypeScript interface | Add to GeneralSettings interface |
| `SettingsPanel.vue` | GUI interface component | Add form element to appropriate tab |

## Common Issues

1. **Setting not appearing in GUI**: Check TypeScript interface and SettingsPanel.vue component
2. **Setting not affecting processing**: Check engine.py mapping
3. **CLI argument not working**: Check schema cli_args and remove any conflicting manual definitions
4. **Type mismatches**: Ensure consistent types across all files
5. **Setting not persisting**: Check dataclass default value
6. **GUI component not working**: Verify correct event handlers and model-value bindings

## Additional Considerations

### Complex Settings
For settings requiring special handling:
- Add validation logic in `getArgs()` (argparser.py)
- Add post-processing in `__post_init__()` (settings_manager.py)
- Add custom UI components in frontend

### Conditional Settings
For settings that depend on others:
- Document dependencies in comments
- Add validation in GUI components
- Consider grouping in settings categories

This unified approach ensures that new settings work consistently across CLI and GUI modes with minimal code duplication.
