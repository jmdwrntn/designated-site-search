import processing

# Print summary of results to console
print('Results:')

# Get the path to the GeoPackage if working with local data
path_to_gpkg = "../designated-site-search/input/data.gpkg"

# Create layers for each designated site data source inside .gpkg
aw = QgsVectorLayer(path_to_gpkg + "|layername=aw", "aw", "ogr")
lnr = QgsVectorLayer(path_to_gpkg + "|layername=lnr", "lnr", "ogr")
nnr = QgsVectorLayer(path_to_gpkg + "|layername=nnr", "nnr", "ogr")
ramsar = QgsVectorLayer(path_to_gpkg + "|layername=ramsar", "ramsar", "ogr")
sac = QgsVectorLayer(path_to_gpkg + "|layername=sac", "sac", "ogr")
sinc = QgsVectorLayer(path_to_gpkg + "|layername=sinc", "sinc", "ogr")
spa = QgsVectorLayer(path_to_gpkg + "|layername=spa", "spa", "ogr")
sssi = QgsVectorLayer(path_to_gpkg + "|layername=sssi", "sssi", "ogr")

# Create layer for your site
site_boundary = QgsVectorLayer("../designated-site-search/input/site_boundary.shp","site_boundary","ogr")

# Create layers from ArcGIS FeatureServers (significantly slower)

# aw = QgsVectorLayer("crs='EPSG:27700' url='https://gis2.london.gov.uk/server/rest/services/apps/planning_data_map_02/MapServer/217'", "aw", "arcgisfeatureserver")
# lnr = QgsVectorLayer("crs='EPSG:27700' url='https://environment.data.gov.uk/arcgis/rest/services/NE/LocalNatureReservesEngland/FeatureServer/0'", "lnr", "arcgisfeatureserver")
# nnr = QgsVectorLayer("crs='EPSG:27700' url='https://environment.data.gov.uk/arcgis/rest/services/NE/NationalNatureReservesEngland/FeatureServer/0'", "nnr", "arcgisfeatureserver")
# ramsar = QgsVectorLayer("crs='EPGS:27700' url='https://environment.data.gov.uk/arcgis/rest/services/NE/RamsarEngland/FeatureServer/0'", "ramsar", "arcgisfeatureserver")
# sac = QgsVectorLayer("crs='EPSG:27700' url='https://environment.data.gov.uk/arcgis/rest/services/NE/SpecialAreasOfConservationEngland/FeatureServer/0'", "sac", "arcgisfeatureserver")
# sinc = QgsVectorLayer("crs='EPSG:27700' url='https://gis2.london.gov.uk/server/rest/services/apps/planning_data_map_02/MapServer/202'", "sinc", "arcgisfeatureserver")
# spa = QgsVectorLayer("crs='EPSG:27700', url='https://environment.data.gov.uk/arcgis/rest/services/NE/SpecialProtectionAreasEngland/FeatureServer/0'", "spa", "arcgisfeatureserver")
# sssi = QgsVectorLayer("crs='EPSG:27700' url='https://gis2.london.gov.uk/server/rest/services/apps/planning_data_map_02/MapServer/203'", "sssi", "arcgisfeatureserver")

# Define symbology for each designated site layer
aw_symbol = QgsLineSymbol.createSimple({'color': '#a7dbdb', 'width': '1.0'})
lnr_symbol = QgsLineSymbol.createSimple({'color': '#e0e4cc', 'width': '1.0'})
nnr_symbol = QgsLineSymbol.createSimple({'color': '#f38630', 'width': '1.0'})
ramsar_symbol = QgsLineSymbol.createSimple({'color': '#309df3', 'width': '1.0'})
sac_symbol = QgsLineSymbol.createSimple({'color': '#542733', 'width': '1.0'})
sinc_symbol = QgsLineSymbol.createSimple({'color': '#5a6a62', 'width': '1.0'})
spa_symbol = QgsLineSymbol.createSimple({'color': '#fdf200', 'width': '1.0'})
sssi_symbol = QgsLineSymbol.createSimple({'color': '#1fda9a', 'width': '1.0'})

# Add designated site layers and symoblogy to dictionary
symbology = {aw: aw_symbol,
            lnr: lnr_symbol,
            nnr: nnr_symbol,
            ramsar: ramsar_symbol,
            sac: sac_symbol,
            sinc: sinc_symbol,
            spa: spa_symbol,
            sssi: sssi_symbol}

# Define expression to calculate line angle from site_boundary to each designated site
bearing = QgsExpression('line_interpolate_angle( $geometry, distance)')

# Define expression to map bearing value to compass direction
direction = QgsExpression(
    """
    CASE
    when "bearing" BETWEEN 337.5 AND 360 OR "bearing" BETWEEN 0 AND 22.5 THEN 'N'
    when "bearing" BETWEEN 22.5 AND 67.5 THEN 'NE'
    when "bearing" BETWEEN 67.5 AND 112.5 THEN 'E'
    when "bearing" BETWEEN 112.5 AND 157.5 THEN 'SE'
    when "bearing" BETWEEN 157.5 AND 202.5 THEN 'S'
    when "bearing" BETWEEN 202.5 AND 247.5 THEN 'SW'
    when "bearing" BETWEEN 247.5 AND 292.5 THEN 'W'
    when "bearing" BETWEEN 292.5 AND 337.5 THEN 'NW'
    END
    """
    )

# Define expressions to add coordinates of line endpoint for labelling    
x_end = QgsExpression('$x_at(-1)')
y_end = QgsExpression('$y_at(-1)')

# Create ExpressionContext object to parse and evaluate expressions
context = QgsExpressionContext()

def site_search(source_layer, site_boundary, distance):
    """
    Calculates distance between features by plotting shortest line.
    Line direction is reversed then bearing and direction are calculated,
    and style is applied to show distance and direction a feature is from the RLB.
    """

    # Apply 'shortestline' algorithm to source_layer and site_boundary, based on distance
    lines = processing.run("native:shortestline", {'SOURCE': source_layer,
            'DESTINATION': site_boundary,
            'DISTANCE': distance,
            'OUTPUT': 'TEMPORARY_OUTPUT'})
    # Save temporary output to a variable   
    lines_out = lines['OUTPUT']

    # Check whether any features were within distance
    line_features = lines_out.featureCount()
    
    # Only continue if any line features created
    if line_features > 0:

        # Apply 'reverselinedirection' algorithm to 'shortestline' output
        reversed = processing.run("native:reverselinedirection",
                {'INPUT': lines_out,
                'OUTPUT': 'TEMPORARY_OUTPUT'})
        # Save temporary output to a variable        
        reversed_out = reversed['OUTPUT']

        # Add attributes for bearing, direction, and label coordinates to temporary output 
        caps = reversed_out.dataProvider().capabilities()
        if caps & QgsVectorDataProvider.AddAttributes:
            res = reversed_out.dataProvider().addAttributes([QgsField('bearing', QVariant.Int),
            QgsField('direction', QVariant.String), QgsField('x_end', QVariant.Double),
            QgsField('y_end', QVariant.Double)])
            reversed_out.updateFields()

        # Apply relevant expression to 'bearing' field
        with edit(reversed_out):
            for f in reversed_out.getFeatures():
                context.setFeature(f)
                f['bearing'] = bearing.evaluate(context)
                reversed_out.updateFeature(f)

        # Apply relevant expression to 'direction' field
        with edit(reversed_out):
            for f in reversed_out.getFeatures():
                context.setFeature(f)
                f['direction'] = direction.evaluate(context)
                reversed_out.updateFeature(f)

        # Apply relevant expression to 'x_end' field
        with edit(reversed_out):
            for f in reversed_out.getFeatures():
                context.setFeature(f)
                f['x_end'] = x_end.evaluate(context)
                reversed_out.updateFeature(f)

        # Apply relevant expression to 'y_end' field
        with edit(reversed_out):
            for f in reversed_out.getFeatures():
                context.setFeature(f)
                f['y_end'] = y_end.evaluate(context)
                reversed_out.updateFeature(f)

        # Apply 'setlayerstyle' algorithm to format layer labels
        processing.run("native:setlayerstyle", {
            'INPUT': reversed_out,
            'STYLE': "../designated-site-search/labels.qml"
        })

        # Use SourceLayer as key in dictionary to retrieve relevant symbol layer
        if source_layer in symbology:
            reversed_out.renderer().setSymbol(symbology[source_layer])

        # Apply symbology change
        reversed_out.triggerRepaint()

        # Add to map as temporary layer
        QgsProject.instance().addMapLayer(reversed_out)
        reversed_out.setName(source_layer.name())

        print(f'{line_features} {source_layer.name()}s found within {distance}m')

        # Export to .csv
        QgsVectorFileWriter.writeAsVectorFormat(reversed_out,
        "../designated-site-search/output/" + source_layer.name() + "s.csv",
        "utf-8", driverName = "CSV")

# Add all source layers to list
layers = [aw, lnr, nnr, ramsar, sac, sinc, spa, sssi]

# Iterate over list, passing each source layer to the site_search function
for layer in layers:
    site_search(layer, site_boundary, 2000)