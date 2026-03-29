import React, { useState } from 'react';
import {
  Box,
  Button,
  FormHelperText,
  TextField,
  MenuItem,
  Select,
  InputLabel,
  FormControl,
  Grid,
  SelectChangeEvent,
  Stack,
  Typography,
  useMediaQuery,
  useTheme,
} from '@mui/material';

export interface AdvancedSearchFilters {
  search?: string;
  category?: string;
  group?: string;
  status?: string;
  sort?: string;
  country?: string;
  language?: string;
  is_active?: string;
  is_online?: string;
}

interface AdvancedSearchProps {
  filters: AdvancedSearchFilters;
  onChange: (filters: AdvancedSearchFilters) => void;
  categories?: string[];
  groups?: string[];
  visibleFields?: Partial<Record<keyof AdvancedSearchFilters, boolean>>;
}

const statusOptions = [
  { value: '', label: 'Any' },
  { value: 'active', label: 'Active' },
  { value: 'inactive', label: 'Inactive' },
  { value: 'online', label: 'Online' },
  { value: 'offline', label: 'Offline' },
];

const sortOptions = [
  { value: '', label: 'Default' },
  { value: 'name', label: 'Name' },
  { value: 'status', label: 'Status' },
  { value: 'category', label: 'Category' },
  { value: 'last_checked', label: 'Last Checked' },
];

const AdvancedSearch: React.FC<AdvancedSearchProps> = ({
  filters,
  onChange,
  categories = [],
  groups = [],
  visibleFields,
}) => {
  const [local, setLocal] = useState<AdvancedSearchFilters>(filters);
  const theme = useTheme();
  const isPhone = useMediaQuery(`(max-width:${theme.appTokens.layout.shell.phoneMaxWidth}px)`);
  const fieldSize = isPhone ? 'medium' : 'small';
  const isFieldVisible = (field: keyof AdvancedSearchFilters) => visibleFields?.[field] !== false;

  React.useEffect(() => {
    setLocal(filters);
  }, [filters]);

  const handleSelectChange = (e: SelectChangeEvent<string>) => {
    const { name, value } = e.target;
    setLocal((prev) => ({ ...prev, [name as string]: value }));
  };

  const handleInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value } = e.target;
    setLocal((prev) => ({ ...prev, [name]: value }));
  };

  const handleApply = () => {
    onChange(local);
  };

  const handleReset = () => {
    setLocal({});
    onChange({});
  };

  const getSelectProps = (name: string, label: string) => ({
    labelId: `${name}-label`,
    id: `${name}-select`,
    name,
    label,
  });

  return (
    <Box component="form" aria-label="Channel filters" onSubmit={(event) => {
      event.preventDefault();
      handleApply();
    }} sx={{ display: 'grid', gap: 2.5 }}>
      <Box>
        <Typography variant="body2" color="text.secondary">
          Narrow the list with names, categories, status, or location details before reviewing the results.
        </Typography>
      </Box>

      <Grid container spacing={2} alignItems="flex-start">
        {isFieldVisible('search') ? (
        <Grid item xs={12} sm={6} md={3}>
          <TextField
            name="search"
            label="Search"
            value={local.search || ''}
            onChange={handleInputChange}
            fullWidth
            size={fieldSize}
            helperText="Search by channel name or number."
          />
        </Grid>
        ) : null}
        {isFieldVisible('category') ? (
        <Grid item xs={12} sm={6} md={2}>
          <FormControl fullWidth size={fieldSize}>
            <InputLabel id="category-label">Category</InputLabel>
            <Select
              {...getSelectProps('category', 'Category')}
              value={local.category || ''}
              onChange={handleSelectChange}
            >
              <MenuItem value="">Any</MenuItem>
              {categories.map(cat => (
                <MenuItem key={cat} value={cat}>{cat}</MenuItem>
              ))}
            </Select>
            <FormHelperText>Limit results to one channel category.</FormHelperText>
          </FormControl>
        </Grid>
        ) : null}
        {isFieldVisible('group') ? (
        <Grid item xs={12} sm={6} md={2}>
          <FormControl fullWidth size={fieldSize}>
            <InputLabel id="group-label">Group</InputLabel>
            <Select
              {...getSelectProps('group', 'Group')}
              value={local.group || ''}
              onChange={handleSelectChange}
            >
              <MenuItem value="">Any</MenuItem>
              {groups.map(grp => (
                <MenuItem key={grp} value={grp}>{grp}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        ) : null}
        {isFieldVisible('status') ? (
        <Grid item xs={12} sm={6} md={2}>
          <FormControl fullWidth size={fieldSize}>
            <InputLabel id="status-label">Status</InputLabel>
            <Select
              {...getSelectProps('status', 'Status')}
              value={local.status || ''}
              onChange={handleSelectChange}
            >
              {statusOptions.map(opt => (
                <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        ) : null}
        {isFieldVisible('sort') ? (
        <Grid item xs={12} sm={6} md={2}>
          <FormControl fullWidth size={fieldSize}>
            <InputLabel id="sort-label">Sort By</InputLabel>
            <Select
              {...getSelectProps('sort', 'Sort By')}
              value={local.sort || ''}
              onChange={handleSelectChange}
            >
              {sortOptions.map(opt => (
                <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        ) : null}
        {isFieldVisible('country') ? (
        <Grid item xs={12} sm={6} md={2}>
          <TextField
            name="country"
            label="Country"
            value={local.country || ''}
            onChange={handleInputChange}
            fullWidth
            size={fieldSize}
            helperText="Use a short country code when you know it."
          />
        </Grid>
        ) : null}
        {isFieldVisible('language') ? (
        <Grid item xs={12} sm={6} md={2}>
          <TextField
            name="language"
            label="Language"
            value={local.language || ''}
            onChange={handleInputChange}
            fullWidth
            size={fieldSize}
            helperText="Use the channel audio language when available."
          />
        </Grid>
        ) : null}
        {isFieldVisible('is_active') ? (
        <Grid item xs={12} sm={6} md={2}>
          <FormControl fullWidth size={fieldSize}>
            <InputLabel id="is_active-label">Active</InputLabel>
            <Select
              {...getSelectProps('is_active', 'Active')}
              value={local.is_active || ''}
              onChange={handleSelectChange}
            >
              <MenuItem value="">Any</MenuItem>
              <MenuItem value="true">Active</MenuItem>
              <MenuItem value="false">Inactive</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        ) : null}
        {isFieldVisible('is_online') ? (
        <Grid item xs={12} sm={6} md={2}>
          <FormControl fullWidth size={fieldSize}>
            <InputLabel id="is_online-label">Online</InputLabel>
            <Select
              {...getSelectProps('is_online', 'Online')}
              value={local.is_online || ''}
              onChange={handleSelectChange}
            >
              <MenuItem value="">Any</MenuItem>
              <MenuItem value="true">Online</MenuItem>
              <MenuItem value="false">Offline</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        ) : null}
        <Grid item xs={12} md={4}>
          <Stack
            data-testid="advanced-search-actions"
            data-layout={isPhone ? 'stacked' : 'inline'}
            direction={{ xs: 'column', sm: 'row' }}
            spacing={1}
            justifyContent="flex-end"
            alignItems="stretch"
          >
            <Button type="submit" variant="contained" color="primary" data-action-priority="primary" fullWidth>
              Apply Filters
            </Button>
            <Button type="button" variant="outlined" color="secondary" onClick={handleReset} data-action-priority="secondary" fullWidth>
              Reset Filters
            </Button>
          </Stack>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AdvancedSearch;
