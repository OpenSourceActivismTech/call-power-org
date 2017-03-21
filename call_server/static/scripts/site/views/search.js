/*global CallPower, Backbone */

(function () {
  CallPower.Views.TargetSearch = Backbone.View.extend({
    el: $('div#target-search'),

    events: {
      // target search
      'keydown input[name="target-search"]': 'searchKey',
      'focusout input[name="target-search"]': 'searchTab',
      'click .search-field .dropdown-menu li': 'searchField',
      'click .search': 'doTargetSearch',
      'click .search-results .result': 'selectSearchResult',
      'click .search-results .close': 'closeSearch',
    },

    initialize: function() { },

    searchKey: function(event) {
      if(event.which === 13) { // enter key
        event.preventDefault();
        this.doTargetSearch();
      }
    },

    searchTab: function(event) {
      // TODO, if there's only one result add it
      // otherwise, let user select one
    },

    searchField: function(event) {
      event.preventDefault();
      var selectedField = $(event.currentTarget).text();
      $('.search-field button').html(selectedField+' <span class="caret"></span>');
      $('input[name=search_field]').val(selectedField.replace(' ', '_').toLowerCase());
    },

    doTargetSearch: function(event) {
      var self = this;

      var campaign_country = $('select[name="campaign_country"]').val();
      var campaign_type = $('select[name="campaign_type"]').val();
      var campaign_state = $('select[name="campaign_state"]').val();
      var search_field = $('input[name=search_field]').val();

      // search the political data cache by default
      var query = $('input[name="target-search"]').val();
      var searchURL = '/political_data/search';
      var searchData = {
        'country': campaign_country,
        'key': query // default to full text search
      };

      if (query.length < 2) {
        return false;
      }

      if (campaign_country === 'us') {
        var chamber = $('select[name="campaign_subtype"]').val();

        if (campaign_type === 'congress') {
          // format key by chamber
          if (search_field === 'state') {
            if (chamber === 'lower') {
                searchData['key'] = 'us:house:'+query;
            }
            if (chamber === 'upper') {
              searchData['key'] = 'us:senate:'+query;
            }
            if (chamber === 'both') {
              // use jQuery param to send multiple values
              searchData = $.param({ 'key': ['us:house:'+query, 'us:senate:'+query] }, true);
            }
          }

          if (search_field === 'last_name') {
            console.error('TODO, search cache by name');
            return false;
          }
        }

        if (campaign_type === 'state') {
          if (chamber === 'exec') {
            searchData['key'] = 'us_state:governor:'+query;
          } else {
            // hit OpenStates
            searchURL = CallPower.Config.SUNLIGHT_STATES_URL;
            searchData = {
              apikey: CallPower.Config.SUNLIGHT_API_KEY,
              state: campaign_state,
            }
            if (chamber === 'upper' || chamber === 'lower') {
              searchData['chamber'] = chamber;
            } // if both, don't limit to a chamber
            searchData[search_field] = query;
          }
        }
      }

      console.log(searchURL, searchData);

      $.ajax({
        url: searchURL,
        data: searchData,
        beforeSend: function(jqXHR, settings) { console.log(settings.url); },
        success: self.renderSearchResults,
        error: self.errorSearchResults,
      });
      return true;
    },

    renderSearchResults: function(response) {
      console.log(response);

      var results;
      if (response.results) {
        results = response.results;
      } else {
        // openstates doesn't paginate
        results = response;
      }

      var dropdownMenu = renderTemplate("#search-results-dropdown-tmpl");
      if (results.length === 0) {
        dropdownMenu.append('<li class="result close"><a>No results</a></li>');
      }

      _.each(results, function(person) {
        // standardize office titles
        if (person.title === 'Sen')  { person.title = 'Senator'; }
        if (person.title === 'Rep')  { person.title = 'Representative'; }

        if (person.bioguide_id) {
          person.uid = 'us:bioguide:'+person.bioguide_id;
        } else if (person.leg_id) {
          person.uid = 'us_state:openstates:'+person.leg_id;
        } else if (person.title === 'Governor') {
          person.uid = 'us_state:governor:'+person.state
        }

        // render the main office
        if (person.phone) {
          var li = renderTemplate("#search-results-item-tmpl", person);
          dropdownMenu.append(li);
        }

        // then any others
        _.each(person.offices, function(office) {
          if (office.phone) {
            person.phone = office.phone;
            person.office_name = office.name || office.city;
            var li = renderTemplate("#search-results-item-tmpl", person);
            dropdownMenu.append(li);
          }
        });
      });
      $('.input-group .search-results').append(dropdownMenu);
    },

    errorSearchResults: function(response) {
      // TODO: show bootstrap warning panel
      console.log(response);
    },

    closeSearch: function() {
      var dropdownMenu = $('.search-results .dropdown-menu').remove();
    },

    selectSearchResult: function(event) {
      // pull json data out of data-object attr
      var obj = $(event.target).data('object');
      
      // add it to the targetListView collection
      CallPower.campaignForm.targetListView.collection.add(obj);

      // if only one result, closeSearch
      if ($('.search-results .dropdown-menu').children('.result').length <= 1) {
        this.closeSearch();
      }
    },

  });

})();