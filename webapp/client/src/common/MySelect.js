import React, { useState, useEffect } from "react";
import { default as ReactSelect, components } from "react-select";
import AsyncSelect from 'react-select/async';
import { WindowedMenuList } from "react-windowed-select";
import { clone } from "lodash";
import { colors } from './Colors';
const selectStyles = { menu: styles => ({ ...styles, zIndex: 999 }) };

//filterable select-all
export const MySelect = props => {
  const [searchField, setSearchField] = useState();
  const [values, setValues] = useState(props.value);

  const isIncludingString = (string, option) => {
    let result = false;
    if (
      !string ||
      option.label.toString().toLowerCase().includes(string) ||
      option.value.toString().toLowerCase().includes(string)
    ) {
      result = true;
    }
    return result;
  }

  const onChange = (opt, { option }) => {
    let newOpts = opt;
    let string = searchField;

    if (option && option.value === "all") {
      let filteredOptions = clone(props.options);

      filteredOptions = filteredOptions.filter(
        filteredOption =>
          isIncludingString(string, filteredOption) &&
          !newOpts.includes(filteredOption)
      );

      string = null;
      newOpts = newOpts
        .concat(filteredOptions)
        .filter(newOpt => newOpt.value !== "all");
    }
    setSearchField(string);
    setValues(newOpts);
    props.onChange(newOpts);
  };

  const onInputChange = (string, { action }) => {
    if (action === "input-change") {
      setSearchField(string);
    }
  };

  const filterOption = ({ label, value }, string) => {
    if (value === "all") {
      return true;
    } else if (string) {
      return label.toLowerCase().includes(string.toLowerCase()) || value.toString().toLowerCase().includes(string.toLowerCase());
    } else {
      return true;
    }
  };

  useEffect(() => {
    if (props.selectAll) {
      //add 'Select All' to menu
      props.options.unshift({ label: "Select All", value: "all" });
    }

  }, [props]);

  return (
    <ReactSelect
      isMulti={props.selectAll ? true : props.isMulti}
      placeholder={props.placeholder}
      filterOption={filterOption}
      onInputChange={onInputChange}
      onChange={onChange}
      options={props.options}
      value={values}
      defaultValue={props.defaultValue? props.defaultValue: null}
      styles={selectStyles}
      formatGroupLabel={formatGroupLabel}

      closeMenuOnSelect={props.closeMenuOnSelect}
      hideSelectedOptions={props.hideSelectedOptions}
      isClearable={props.isClearable}
      
      components={props.checkbox ? {
        Option, MultiValue
      } : {}}

      theme={theme => ({
        ...theme,
        borderRadius: '5px',
        colors: {
          ...theme.colors,
          primary: colors.primary,
        },
      })}
    />
  );
}

export const Option = props => {
  return (
    <div>
      <components.Option {...props}>
        {props.label !== 'Select All' &&
          <input
            type="checkbox"
            checked={props.isSelected}
            onChange={() => null}
          />
        }
        {" "}
        <label>{props.label}</label>
      </components.Option>
    </div>
  );
};

export const MultiValue = props => (
  <components.MultiValue {...props}>
    <span>{props.data.label}</span>
  </components.MultiValue>
);

const groupStyles = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
};
const groupBadgeStyles = {
  backgroundColor: '#EBECF0',
  borderRadius: '2em',
  color: '#172B4D',
  display: 'inline-block',
  fontSize: 12,
  fontWeight: 'normal',
  lineHeight: '1',
  minWidth: 1,
  padding: '0.16666666666667em 0.5em',
  textAlign: 'center',
};

const formatGroupLabel = data => (
  <div style={groupStyles}>
    <span>{data.label}</span>
    <span style={groupBadgeStyles}>{data.options.length}</span>
  </div>
);

//async select with windowed menu list for large dataset
export const MyAsyncSelect = props => {
  const [inputValue, setInputValue] = useState();
  const [selected, setSelected] = useState([]);
  const [filteredOptions, setFilteredOptions] = useState([]);
  const [reload, setReload] = useState(0);

  const onChange = (opt, { option }) => {
    let newOpts = opt;
    if (option && option.value === "all" && props.isMulti) {
      newOpts = newOpts
        .concat(filteredOptions)
        .filter(newOpt => newOpt.value !== "all");
      setInputValue('');
    }

    if (!option || newOpts.length >= props.maxSelected) {
      //after delete an option
      setInputValue('');
      setReload(reload + 1);
    }
    if (!newOpts && props.isMulti) {
      newOpts = [];
    }
    setSelected(newOpts)
    props.onChange(newOpts);
  };

  const onInputChange = (newValue, { action }) => {
    if (action === "input-change") {
      const inputValue = newValue;
      setInputValue(inputValue);
      return inputValue;
    }
    //keep seach input
    return inputValue;
  };

  const filterOptions = () => {
    if (!inputValue || (props.isMulti && props.maxSelected && selected.length >= props.maxSelected)) {
      return false;
    }

    let parts = inputValue.split(/\s+/);

    let options = props.options.filter(opt => {
      //match any term
      //return parts.some(term=> opt.label.toLowerCase().includes(term.toLowerCase()));
      //match all term 
      return parts.every(term => opt.label.toLowerCase().includes(term.toLowerCase()));
    });

    //selected options length + current filtered options length, used for determining whether adding 'Select All' option to option list
    let size = 0;

    if (props.isMulti) {
      size += selected.length;
      options = options.filter(opt => {
        //not in selected options
        return selected.every(option => opt.value !== option.value);
      });
    }

    size += options.length;

    if (options.length > 0) {
      if (props.isMulti && props.selectAll) {
        if (props.maxSelected) {
          if (size <= props.maxSelected) {
            //add 'Select All' to menu
            options.unshift({ label: "Select All (" + options.length + "). Selection status: " + selected.length + "/" + props.maxSelected, value: "all" });
          } else {
            options.unshift({ label: "Results (" + options.length + "). Selection status: " + selected.length + "/" + props.maxSelected, value: "results", isDisabled: true });
          }
        } else {
          options.unshift({ label: "Select All (" + options.length + ")", value: "all" });
        }
      } else {
        //show number of available options
        options.unshift({ label: "Results (" + options.length + ")", value: "results", isDisabled: true });
      }
    }

    setFilteredOptions(options);
    return options;
  };

  const promiseOptions = () =>
    new Promise(resolve => {
      setTimeout(() => {
        resolve(filterOptions());
      }, 1000);
    });

  return (
    <AsyncSelect
      classNamePrefix="mySelect"
      isMulti={props.isMulti}
      isClearable={true}
      placeholder={props.placeholder}
      loadOptions={promiseOptions}
      onChange={onChange}
      onInputChange={onInputChange}
      value={selected}
      inputValue={inputValue}
      styles={selectStyles}

      //reload options
      key={reload}

      blurInputOnSelect={false}
      closeMenuOnSelect={props.closeMenuOnSelect}
      hideSelectedOptions={props.hideSelectedOptions}

      autoload={false}
      noOptionsMessage={() => props.noOptionsMessage}
      //use windowed list for large dataset
      components={{ MenuList: WindowedMenuList }}

      theme={theme => ({
        ...theme,
        borderRadius: '5px',
        colors: {
          ...theme.colors,
          primary: colors.primary,
        },
      })}

    />
  );
}

//display 'Select All..' rather than real options to address slow rendering large selected options
export const MyAsyncSelect2 = props => {
  const [inputValue, setInputValue] = useState();
  const [selected, setSelected] = useState([]);
  const [selectedShow, setSelectedShow] = useState([]);
  const [filteredOptions, setFilteredOptions] = useState([]);
  //const [selectAllMap, setSelectAllMap] = useState({});
  let selectAllMap = {};
  const [reload, setReload] = useState(0);

  const onChange = (opt, { option }) => {
    let newOpts = opt;
    if (option && option.value === "all " + inputValue) {
      //add to map
      selectAllMap["all " + inputValue] = filteredOptions.filter(newOpt => newOpt.value !== "all " + inputValue);
      setInputValue('');
    }

    if (!newOpts) {
      newOpts = [];
    }
    if (!option) {
      //after delete an option
      Object.keys(selectAllMap).forEach(key => {
        if (!newOpts.some(option => option.value === key)) {
          delete selectAllMap[key];
        }
      });
      setInputValue('');
      setReload(reload + 1);
    }
    //filter out 'all ' selections
    newOpts = newOpts.filter(opt => !opt.value.startsWith('all '));
    //add real selections for 'all '
    Object.keys(selectAllMap).forEach(key => {
      newOpts = newOpts.concat(selectAllMap[key]);
    });
    //remove duplicated values just in case
    newOpts = [...new Set(newOpts)];
    console.log('real', newOpts)
    setSelectedShow(opt);
    setSelected(newOpts)
    props.onChange(newOpts);
  };

  const onInputChange = (newValue, { action }) => {
    if (action === "input-change") {
      const inputValue = newValue;
      setInputValue(inputValue);
      return inputValue;
    }
    //keep seach input
    return inputValue;
  };

  const filterOptions = () => {
    if (!inputValue || inputValue.length < 3 ) {
      return false;
    }

    let parts = inputValue.split(/\s+/);

    let options = props.options.filter(opt => {
      //match any term
      //return parts.some(term=> opt.label.toLowerCase().includes(term.toLowerCase()));
      //match all term and not in selected list
      return parts.every(term => opt.label.toLowerCase().includes(term.toLowerCase())) && selected.every(option => opt.value !== option.value);
    });

    setFilteredOptions(options);
    const size = options.length;
    if (size > 0) {
      options.unshift({ label: "Select All (" + size + ") '" + inputValue + "'", value: "all " + inputValue });
    }

    return options;
  };

  const promiseOptions = () =>
    new Promise(resolve => {
      setTimeout(() => {
        resolve(filterOptions());
      }, 100);
    });

  return (
    <AsyncSelect
      classNamePrefix="mySelect"
      isMulti={props.isMulti}
      isClearable={true}
      placeholder={props.placeholder}
      loadOptions={promiseOptions}
      onChange={onChange}
      onInputChange={onInputChange}
      value={selectedShow}
      inputValue={inputValue}
      styles={selectStyles}

      //reload options
      key={reload}

      blurInputOnSelect={false}
      closeMenuOnSelect={props.closeMenuOnSelect}
      hideSelectedOptions={props.hideSelectedOptions}

      autoload={false}
      noOptionsMessage={() => props.noOptionsMessage}
      //use windowed list for large dataset
      components={{ MenuList: WindowedMenuList }}

      theme={theme => ({
        ...theme,
        borderRadius: '5px',
        colors: {
          ...theme.colors,
          primary: colors.primary,
        },
      })}

    />
  );
}

export default MySelect;