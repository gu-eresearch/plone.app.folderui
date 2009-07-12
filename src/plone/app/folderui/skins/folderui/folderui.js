
function toggle_facet() {
    context = jQuery(this).parent();
    jQuery('.facetmenu', context).toggle();
}

function facet_helper() {
    jQuery('div.searchfilter h3').bind('click', toggle_facet);
    /* jQuery('div.searchfilter ul').toggle(); */
}

jQuery(document).ready(facet_helper);

