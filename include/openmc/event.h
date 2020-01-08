#ifndef OPENMC_EVENT_H
#define OPENMC_EVENT_H

#include "openmc/particle.h"
#include "openmc/tallies/filter.h"

#include <vector>


namespace openmc {

//==============================================================================
// Structs
//==============================================================================

struct QueueItem{
  int idx;      // particle index in event-based buffer
  double E;     // particle energy
  int material; // material that particle is in
  Particle::Type type;
  bool operator<(const QueueItem & rhs) const
  {
    // First, compare by type
    if( type < rhs.type )
      return true;
    if( type > rhs.type )
      return false;

    // At this point, we have the same particle types.
    // Now, compare by material

    // TODO: Temporarily disabled as SMR problem has different material IDs for every pin
    // Need to sort by material type instead...
    /*
       if( material < rhs.material)
       return true;
       if( material > rhs.material)
       return false;
       */

    // At this point, we have the same particle type, in the same material.
    // Now, compare by energy
    return (E < rhs.E);
  }
};

//==============================================================================
// Global variable declarations
//==============================================================================
//
namespace simulation {

extern QueueItem * calculate_fuel_xs_queue;
extern QueueItem * calculate_nonfuel_xs_queue;
extern QueueItem * advance_particle_queue;
extern QueueItem * surface_crossing_queue;
extern QueueItem * collision_queue;
extern Particle * particles;
extern int calculate_fuel_xs_queue_length;
extern int calculate_nonfuel_xs_queue_length;
extern int advance_particle_queue_length;
extern int surface_crossing_queue_length;
extern int collision_queue_length;
extern int max_particles_in_flight;

} // namespace simulation

//==============================================================================
// Functions
//==============================================================================

void init_event_queues(int n_particles);
void free_event_queues(void);
void dispatch_xs_event(int i);
void process_calculate_xs_events(QueueItem * queue, int n);
void process_advance_particle_events();
void process_surface_crossing_events();
void process_collision_events();

} // namespace openmc

#endif // OPENMC_EVENT_H
