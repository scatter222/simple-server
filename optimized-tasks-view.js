import classes from '../../styles/Deploy.module.css';
import React, { useEffect, useMemo, useCallback, useState } from "react";
import Tabs from '@mui/material/Tabs';
import Tab from '@mui/material/Tab';
import TaskCard from '../Cards/TaskCard';
import HistoryTab from '../HistoryTab';
import { TabPanel } from './TabPanel';
import Chip from '@mui/material/Chip';
import { CircularProgress, TextField } from '@mui/material';
import { useSearchParams, useNavigate } from 'react-router-dom';
import { List, AutoSizer, WindowScroller } from 'react-virtualized';
import { debounce } from 'lodash';

// Extract unique tags from data - moved outside component as pure function
function getUniqueTagsFromData(data) {
  const tags = data.flatMap(task => task.tags || []);
  return [...new Set(tags)];
}

export function AllTasksView({ value, handleChange, data, handleChangeTask, viewRunningTask, runDeploymentHandler, playbookType }) {
  // State management
  const [allTags, setAllTags] = useState([]);
  const [selectedTags, setSelectedTags] = useState([]);
  const [searchTerm, setSearchTerm] = useState('');
  const [filteredData, setFilteredData] = useState([]);
  const [isLoading, setIsLoading] = useState(false);

  // Debounced search handler to prevent excessive filtering
  const debouncedSearchHandler = useCallback(
    debounce((value) => {
      setSearchTerm(value);
    }, 300),
    []
  );

  // Memoized tag handling for better performance
  const handleTagChipClick = useCallback((tag) => {
    setSelectedTags(prevTags => 
      prevTags.includes(tag) 
        ? prevTags.filter(t => t !== tag) 
        : [...prevTags, tag]
    );
  }, []);

  // Memoized filtering logic to prevent unnecessary calculations
  const getFilteredData = useMemo(() => {
    // Start loading state
    setIsLoading(true);
    
    let result = [...data];

    // Apply search filter if needed
    if (searchTerm) {
      const lowercaseTerm = searchTerm.toLowerCase();
      result = result.filter(task => 
        (task.playbookName?.toLowerCase().includes(lowercaseTerm)) ||
        (task.playbookDescription?.toLowerCase().includes(lowercaseTerm))
      );
    }

    // Apply tag filter if needed
    if (selectedTags.length > 0) {
      result = result.filter(task => 
        task.tags && selectedTags.every(tag => task.tags.includes(tag))
      );
    }

    // End loading state
    setIsLoading(false);
    
    return result;
  }, [data, searchTerm, selectedTags]);

  // Set all available tags once data is loaded
  useEffect(() => {
    if (data && data.length > 0) {
      setAllTags(getUniqueTagsFromData(data));
    }
  }, [data]);

  // Update filtered data when filters change
  useEffect(() => {
    setFilteredData(getFilteredData);
  }, [getFilteredData]);

  // Row renderer for virtualized list
  const rowRenderer = useCallback(({ index, key, style }) => {
    const task = filteredData[index];
    
    if (!task) return null;
    
    return (
      <div key={key} style={style}>
        <TaskCard
          id={index}
          taskId={task.id}
          name={task.playbookName}
          description={task.playbookDescription}
          lastExecution={task.lastExecution}
          viewRunningTask={viewRunningTask}
          onClick={() => handleChangeTask(task)}
          runDeploymentHandler={runDeploymentHandler}
          playbookType={playbookType}
          isLoading={false}
        />
      </div>
    );
  }, [filteredData, handleChangeTask, viewRunningTask, runDeploymentHandler, playbookType]);

  return (
    <div className={classes.contentContainer}>
      <Tabs
        orientation="vertical"
        variant="scrollable"
        value={value}
        onChange={handleChange}
        aria-label="Vertical tabs example"
        sx={{
          marginRight: '30px',
          borderLeft: 1,
          borderColor: 'var(--dark-border-color)',
          '& .MuiTabs-indicator': {
            backgroundColor: 'var(--blue-accent)',
            width: '3px',
            right: 'none',
            left: 0
          },
        }}>
        <Tab sx={{
          '&.Mui-selected': {
            color: 'var(--blue-accent)'
          },
          textTransform: 'none',
          color: 'var(--dark-text-color)',
          fontWeight: 600,
          fontSize: '18px'
        }} label="Tasks" />
        <Tab sx={{
          '&.Mui-selected': {
            color: 'var(--blue-accent)'
          },
          textTransform: 'none',
          color: 'var(--dark-text-color)',
          fontWeight: 600,
          fontSize: '18px'
        }} label="History" />
      </Tabs>
      <TabPanel value={value} index={0}>
        <div className={classes.taskCardContainer}>
          <div className={classes.taskViewActions}>
            <div className={classes.searchContainer}>
              <TextField 
                id="task-search" 
                label="Search Term" 
                variant="standard"
                onChange={(e) => debouncedSearchHandler(e.target.value)}
                sx={{
                  '& label': {
                    color: 'var(--dark-bold-text-color)',
                  },
                  '& .MuiInput-root': {
                    '&:before': {
                      borderColor: 'var(--dark-bold-text-color)',
                    },
                    '&:after': {
                      borderColor: 'var(--blue-accent)',
                    },
                    color: 'var(--dark-bold-text-color)'
                  }
                }} 
              />
            </div>

            {allTags.length > 0 && (
              <div className={classes.chipContainer}>
                {selectedTags.map(tag => (
                  <div key={`selected-${tag}`}>
                    <Chip 
                      sx={{
                        color: 'var(--dark-bold-text-color)',
                        backgroundColor: 'var(--blue-accent)',
                        fontWeight: 600,
                        margin: '2px 5px',
                        '&:hover': {
                          backgroundColor: 'var(--blue-accent)',
                        }
                      }}
                      label={tag}
                      onClick={() => handleTagChipClick(tag)}
                      onDelete={() => handleTagChipClick(tag)} 
                    />
                  </div>
                ))}
                
                {allTags
                  .filter(tag => !selectedTags.includes(tag))
                  .map(tag => (
                    <div key={`available-${tag}`}>
                      <Chip 
                        sx={{
                          color: 'var(--dark-text-color)',
                          borderColor: 'var(--dark-text-color)',
                          margin: '2px 5px'
                        }}
                        label={tag}
                        variant="outlined"
                        onClick={() => handleTagChipClick(tag)} 
                      />
                    </div>
                  ))
                }
              </div>
            )}
          </div>

          {isLoading ? (
            <CircularProgress sx={{ color: 'var(--blue-accent)' }} />
          ) : (
            <div className={classes.cardFlex} style={{ height: 'calc(100vh - 200px)', width: '100%' }}>
              <WindowScroller>
                {({ height, isScrolling, onChildScroll, scrollTop }) => (
                  <AutoSizer disableHeight>
                    {({ width }) => (
                      <List
                        autoHeight
                        height={height || 800}
                        isScrolling={isScrolling}
                        onScroll={onChildScroll}
                        rowCount={filteredData.length}
                        rowHeight={220} // Adjust based on your card height
                        rowRenderer={rowRenderer}
                        scrollTop={scrollTop}
                        width={width}
                        overscanRowCount={5} // Render extra rows above/below viewport
                      />
                    )}
                  </AutoSizer>
                )}
              </WindowScroller>
            </div>
          )}
        </div>
      </TabPanel>
      <TabPanel value={value} index={1}>
        <HistoryTab viewRunningTask={viewRunningTask} />
      </TabPanel>
    </div>
  );
}
