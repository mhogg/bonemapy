    subroutine vusdfld(nblock, nstatev, nfieldv, nprops, ndir, nshr, jElem, &
        kIntPt, kLayer, kSecPt, stepTime, totalTime, dt, cmname, coordMp,   &
        direct, T, charLength, props, stateOld, stateNew, field)

    include 'vaba_param.inc'

    dimension jElem(nblock), coordMp(nblock,*), direct(nblock,3,3), &
              T(nblock,3,3), charLength(nblock), props(nprops),     &
              stateOld(nblock,nstatev), stateNew(nblock,nstatev),   &
              field(nblock,nfieldv)
    character*80 cmname

    integer, parameter :: chunk_size=1000
    integer :: indx(1), indx1(1), indx2(1), ios, n, elmnum, nintp, num_elems, num_parts
    integer, save :: do_once=0
    integer, allocatable, save :: elems_intnum(:)
    real :: huval, density, emodulus, rho_min, rho_max
    real, save :: HUmin, HUmax
    real, allocatable, save :: HU(:,:)
    character(len=80) :: partname
    character(len=256) :: outdir, mat_props, mat_props_path
    character(len=80), allocatable :: partnames(:), temp_partnames(:)

    ! Define a custom array type that contains multiple arrays of different sizes
    ! Reference: https://stackoverflow.com/questions/18316592/multidimensional-array-with-different-lengths
    type t_raggedarray
        integer, allocatable :: locnum(:), intnum(:)
    end type t_raggedarray
    type(t_raggedarray), allocatable :: part_elems(:)

    type t_hudata
        character(len=80):: partname
        integer :: elmnum
        integer :: nintp
        real :: huval
    end type t_hudata
    type(t_hudata) :: hudatai
    type(t_hudata), allocatable :: hudata(:), temp_hudata(:)

    ! Define variables
    mat_props = 'HUvalues.txt'  ! Filename of file containing HU values
    rho_min   = 0.1             ! Minimum apparent bone density (g/cm3)
    rho_max   = 1.7             ! Maximum apparent bone density (g/cm3)

    if (do_once/=1) then

        do_once = 1

        ! Read the HUvalues.txt file
        ! Reference: https://degenerateconic.com/dynamically-sizing-arrays.html
        CALL VGETOUTDIR(outdir, lenoutdir)
        mat_props_path = trim(adjustl(outdir)) // '/' // mat_props
        open(unit=101, file=mat_props_path, status='OLD', action='READ')

        n = 0
        readx: do

            read(101,*,iostat=ios) hudatai

            if (ios/=0) then
                ! NOTE: temp = hudata(1:n) should work here even without the allocate(temp(n)),
                ! but crashes during packaging. However, temp(1:n) does not cause a crash
                if (allocated(temp_hudata)) deallocate(temp_hudata)
                allocate(temp_hudata(n))
                temp_hudata(1:n) = hudata(1:n)
                call move_alloc(from=temp_hudata, to=hudata)
                exit readx
            end if

            if (allocated(hudata)) then
                if (n == size(hudata)) then
                    allocate(temp_hudata(size(hudata) + chunk_size))
                    temp_hudata(1:size(hudata)) = hudata
                    call move_alloc(from=temp_hudata, to=hudata)
                end if
                n = n + 1
            else
                allocate(hudata(chunk_size))
                n = 1
            end if
            hudata(n) = hudatai

        end do readx
        close(101)

        ! Get number of parts
        allocate(partnames(0))
        do i=1,size(hudata)
            partname = upcase(hudata(i)%partname)
            if (ANY(partnames==partname)==.FALSE.) then
                allocate(temp_partnames(1:size(partnames)+1))
                temp_partnames(1:size(partnames)) = partnames(:)
                temp_partnames(size(partnames)+1) = partname
                call move_alloc(temp_partnames, partnames)
            end if
        end do
        num_parts = size(partnames)

        write(*,*) 'Number of parts = ', num_parts

        ! Get element indices for each part
        allocate(part_elems(num_parts))
        do i=1,num_parts

            ! First get the number of elements per part to size the array
            num_elems = 0
            do j=1,size(hudata)
                partname = upcase(hudata(j)%partname)
                if (partname==partnames(i) .and. hudata(j)%nintp==1) num_elems = num_elems + 1
            end do
            allocate(part_elems(i)%locnum(num_elems), part_elems(i)%intnum(num_elems))

            write(*,*) 'Number of elements for part ', trim(partname), ' = ', num_elems

            ! Add the element indices data to the array
            n = 0
            do j=1,size(hudata)
                partname = upcase(hudata(j)%partname)
                if (partname==partnames(i) .and. hudata(j)%nintp==1) then
                    n = n + 1
                    locnum = hudata(j)%elmnum
                    call VGETINTERNAL(partname, locnum, 1, intnum, jrcd)
                    if (jrcd==1) write(*,*) 'Error converting from local to global element numbering'
                    part_elems(i)%intnum(n) = intnum
                    part_elems(i)%locnum(n) = locnum
                end if
            end do

        end do

        ! Get number of elements for all parts and put all global element indices within a single array
        ! Note: We are assuming 4 integration points per element, which only works for a quadratic tet element C3D10 and similar
        num_elems = 0
        do i=1,num_parts
            num_elems = num_elems + size(part_elems(i)%locnum)
        end do
        allocate(elems_intnum(num_elems))
        allocate(HU(num_elems,4))

        n = 0
        do i=1,num_parts
            do j=1,size(part_elems(i)%intnum)
                n = n + 1
                elems_intnum(n) = part_elems(i)%intnum(j)
            end do
        end do

        ! Set the HU values
        HUmin = hudata(1)%huval
        HUmax = hudata(1)%huval
        do i=1,size(hudata)

            partname = upcase(hudata(i)%partname)
            locnum = hudata(i)%elmnum
            nintp = hudata(i)%nintp
            huval = hudata(i)%huval

            if (huval<HUmin) HUmin=huval
            if (huval>HUmax) HUmax=huval

            indx = findloc(partnames, partname)
            indx1 = findloc(part_elems(indx(1))%locnum, locnum)
            intnum = part_elems(indx(1))%intnum(indx1(1))
            indx2 = findloc(elems_intnum, intnum)
            HU(indx2(1),nintp) = huval

        end do

        write(*,*) 'HUmin = ', HUmin
        write(*,*) 'HUmax = ', HUmax

    end if

    ! Set the field of the material points. Note that:
    ! - A block of elements are processed together, where nblock is the number of elements in the block. Typically nblock=144.
    ! - For each call of the subroutine, the integration point number kIntPt is the same for all elements in the block.
    ! - jElem is an array of element numbers for the block, so jElem(k) is the (global, or internal) element number
    ! - stateOld will typically be initialised to 0.0, so this can be used as a flag to determine if material properties
    !   have already been set for that material point
    do k=1, nblock

        if (stateOld(k,1)/=1.0) then
            intnum = jElem(k)
            indx = findloc(elems_intnum, intnum)
            huval = HU(indx(1),kIntPt)
            density = HUtoAppDensity(huval,HUmin,HUmax,rho_min,rho_max)
            emodulus = EfromAppDensity(density,2)
        else
            huval = stateOld(k,2)
            density = stateOld(k,3)
            emodulus = stateOld(k,4)
        end if
        stateNew(k,1) = 1.0
        stateNew(k,2) = huval
        stateNew(k,3) = density
        stateNew(k,4) = emodulus
        field(k,1)    = emodulus

    end do

    ! --------------

    ! User defined functions
    contains

    function upcase(string) result(upper)
    character(len=*), intent(in) :: string
    character(len=len(string)) :: upper
    integer :: j
        do j = 1,len(string)
            if(string(j:j) >= "a" .and. string(j:j) <= "z") then
                upper(j:j) = achar(iachar(string(j:j)) - 32)
        else
            upper(j:j) = string(j:j)
        end if
    end do
    end function upcase

    ! --------------

    function HUtoAppDensity(huval,humin,humax,rhomin,rhomax) result(appdensity)
    real, intent(in)  :: huval,humin,humax,rhomin,rhomax
    real :: appdensity

    ! Linearly converts the HU to apparent density with the following limits:
    ! rho = rhomin at humin
    ! rho = rhomax at humax

    appdensity = rhomin + (rhomax-rhomin)*((huval-humin)/(humax-humin))

    end function HUtoAppDensity

    ! --------------

    function EfromAppDensity(appdensity,choice) result(Evalue)
    real, intent(in) :: appdensity
    real :: Evalue, snrate
    integer, intent(in) :: choice

    ! Converts from apparent bone density (g/cm3) to Elastic Modulus (MPa)
    ! A number of relationships can be used, depending on the value of "choice":
    ! (1) Carter and Hayes, 1977
    ! (2) Morgan et al, 2003

    select case(choice)
    case (1)
        snrate = 0.01
        Evalue = 3790*(snrate**0.06)*(appdensity**3)
    case (2)
        Evalue = 6950*(appdensity**1.49)
    end select

    end function EfromAppDensity

    ! --------------

    end
