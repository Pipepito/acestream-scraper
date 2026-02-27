import React, { useState } from 'react';
import { Box, Button, TextField, MenuItem, Select, InputLabel, FormControl, Grid, SelectChangeEvent } from '@mui/material';

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

const AdvancedSearch: React.FC<AdvancedSearchProps> = ({ filters, onChange, categories = [], groups = [] }) => {
  const [local, setLocal] = useState<AdvancedSearchFilters>(filters);

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

  return (
    <Box mb={2}>
      <Grid container spacing={2} alignItems="center">
        <Grid item xs={12} sm={3}>
          <TextField
            name="search"
            label="Search"
            value={local.search || ''}
            onChange={handleInputChange}
            fullWidth
          />
        </Grid>
        <Grid item xs={12} sm={2}>
          <FormControl fullWidth>
            <InputLabel>Category</InputLabel>
            <Select
              name="category"
              value={local.category || ''}
              label="Category"
              onChange={handleSelectChange}
            >
              <MenuItem value="">Any</MenuItem>
              {categories.map(cat => (
                <MenuItem key={cat} value={cat}>{cat}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={2}>
          <FormControl fullWidth>
            <InputLabel>Group</InputLabel>
            <Select
              name="group"
              value={local.group || ''}
              label="Group"
              onChange={handleSelectChange}
            >
              <MenuItem value="">Any</MenuItem>
              {groups.map(grp => (
                <MenuItem key={grp} value={grp}>{grp}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={2}>
          <FormControl fullWidth>
            <InputLabel>Status</InputLabel>
            <Select
              name="status"
              value={local.status || ''}
              label="Status"
              onChange={handleSelectChange}
            >
              {statusOptions.map(opt => (
                <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={2}>
          <FormControl fullWidth>
            <InputLabel>Sort By</InputLabel>
            <Select
              name="sort"
              value={local.sort || ''}
              label="Sort By"
              onChange={handleSelectChange}
            >
              {sortOptions.map(opt => (
                <MenuItem key={opt.value} value={opt.value}>{opt.label}</MenuItem>
              ))}
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={2}>
          <TextField
            name="country"
            label="Country"
            value={local.country || ''}
            onChange={handleInputChange}
            fullWidth
          />
        </Grid>
        <Grid item xs={12} sm={2}>
          <TextField
            name="language"
            label="Language"
            value={local.language || ''}
            onChange={handleInputChange}
            fullWidth
          />
        </Grid>
        <Grid item xs={12} sm={2}>
          <FormControl fullWidth>
            <InputLabel>Active</InputLabel>
            <Select
              name="is_active"
              value={local.is_active || ''}
              label="Active"
              onChange={handleSelectChange}
            >
              <MenuItem value="">Any</MenuItem>
              <MenuItem value="true">Active</MenuItem>
              <MenuItem value="false">Inactive</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={2}>
          <FormControl fullWidth>
            <InputLabel>Online</InputLabel>
            <Select
              name="is_online"
              value={local.is_online || ''}
              label="Online"
              onChange={handleSelectChange}
            >
              <MenuItem value="">Any</MenuItem>
              <MenuItem value="true">Online</MenuItem>
              <MenuItem value="false">Offline</MenuItem>
            </Select>
          </FormControl>
        </Grid>
        <Grid item xs={12} sm={1}>
          <Button variant="contained" color="primary" onClick={handleApply} sx={{ mr: 1 }}>Apply</Button>
          <Button variant="outlined" color="secondary" onClick={handleReset}>Reset</Button>
        </Grid>
      </Grid>
    </Box>
  );
};

export default AdvancedSearch;
