import generate_playlists
import random
generate_playlists.logging.info('Process Start!')
artist_names = generate_playlists.get_artists_array_names()
if len(artist_names) > 0:
    
    generate_playlists.my_reccommendations()
    random.shuffle(artist_names)
    for artist_name in artist_names:
        generate_playlists.show_recommendations_for_artist(artist_name)
    generate_playlists.get_user_playlists()
    generate_playlists.logging.info('Process Done!')

else:
    generate_playlists.logging.error('No artists found! Your library looks empty!')